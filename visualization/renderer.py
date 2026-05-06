"""
visualization/renderer.py — Pygame Renderer cho Virtual World

Render thế giới ảo với:
    - Grid có màu sắc cho từng loại entity
    - Agents với energy bar và trail
    - Sensor rays (tùy chọn)
    - HUD: stats, episode, epsilon, reward...
    - Panel bên phải: leaderboard agents
"""
import pygame
import numpy as np
import math
from typing import List, Optional

import config as cfg
from core.world import VirtualWorld, DIRECTIONS
from core.agent import WorldAgent, AgentType
from core.entities import EntityType


# Font sizes
FONT_SM = 13
FONT_MD = 16
FONT_LG = 22
FONT_XL = 32

HUD_WIDTH = 260   # Chiều rộng panel HUD bên phải


class Renderer:
    """
    Pygame Renderer — vẽ toàn bộ world + HUD.
    """

    def __init__(self, world: VirtualWorld):
        pygame.init()
        pygame.font.init()

        self.world = world
        self.cell = cfg.VISUAL.cell_size
        self.W = world.W
        self.H = world.H

        screen_w = self.W * self.cell + HUD_WIDTH
        screen_h = self.H * self.cell

        self.screen = pygame.display.set_mode((screen_w, screen_h))
        pygame.display.set_caption("🤖 AI Virtual World — Q-Learning & DQN")

        # Fonts
        try:
            self.font_sm = pygame.font.SysFont("Segoe UI", FONT_SM)
            self.font_md = pygame.font.SysFont("Segoe UI", FONT_MD)
            self.font_lg = pygame.font.SysFont("Segoe UI", FONT_LG, bold=True)
            self.font_xl = pygame.font.SysFont("Segoe UI", FONT_XL, bold=True)
        except Exception:
            self.font_sm = pygame.font.Font(None, FONT_SM + 4)
            self.font_md = pygame.font.Font(None, FONT_MD + 4)
            self.font_lg = pygame.font.Font(None, FONT_LG + 4)
            self.font_xl = pygame.font.Font(None, FONT_XL + 4)

        self.clock = pygame.time.Clock()
        self.episode = 0
        self.total_food_eaten = 0

        # Surfaces
        self.world_surf = pygame.Surface((self.W * self.cell, self.H * self.cell))
        self.hud_surf = pygame.Surface((HUD_WIDTH, screen_h))

    # ─────────────────────────────────────────────────────────────────────────
    # MAIN RENDER
    # ─────────────────────────────────────────────────────────────────────────

    def render(self, agents: List[WorldAgent], episode: int, paused: bool = False):
        """Render một frame đầy đủ."""
        self.episode = episode
        self._draw_world(agents)
        self._draw_hud(agents, paused)

        self.screen.blit(self.world_surf, (0, 0))
        self.screen.blit(self.hud_surf, (self.W * self.cell, 0))

        pygame.display.flip()
        self.clock.tick(cfg.VISUAL.fps)

    # ─────────────────────────────────────────────────────────────────────────
    # WORLD DRAWING
    # ─────────────────────────────────────────────────────────────────────────

    def _draw_world(self, agents: List[WorldAgent]):
        """Vẽ background, grid, entities, trails, sensors, agents."""
        self.world_surf.fill(cfg.VISUAL.COLOR_BG)
        self._draw_grid()
        self._draw_entities()
        if cfg.VISUAL.show_trails:
            self._draw_trails(agents)
        if cfg.VISUAL.show_sensors:
            self._draw_sensors(agents)
        self._draw_agents(agents)

    def _draw_grid(self):
        """Vẽ lưới nhẹ."""
        c = cfg.VISUAL.COLOR_GRID
        for x in range(0, self.W * self.cell, self.cell):
            pygame.draw.line(self.world_surf, c, (x, 0), (x, self.H * self.cell), 1)
        for y in range(0, self.H * self.cell, self.cell):
            pygame.draw.line(self.world_surf, c, (0, y), (self.W * self.cell, y), 1)

    def _draw_entities(self):
        """Vẽ Food, Hazard, Obstacle."""
        cell = self.cell
        pad = 3

        for (x, y), food in self.world.foods.items():
            rect = pygame.Rect(x * cell + pad, y * cell + pad,
                               cell - pad*2, cell - pad*2)
            pygame.draw.ellipse(self.world_surf, cfg.VISUAL.COLOR_FOOD, rect)
            # Glow effect
            glow = pygame.Surface((cell, cell), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (*cfg.VISUAL.COLOR_FOOD, 40),
                                 (0, 0, cell, cell))
            self.world_surf.blit(glow, (x * cell, y * cell))

        for (x, y) in self.world.hazards:
            rect = pygame.Rect(x * cell + pad, y * cell + pad,
                               cell - pad*2, cell - pad*2)
            pygame.draw.rect(self.world_surf, cfg.VISUAL.COLOR_HAZARD, rect,
                              border_radius=3)
            # X mark
            c = cfg.VISUAL.COLOR_HAZARD
            cx, cy = x * cell + cell//2, y * cell + cell//2
            r = cell//4
            pygame.draw.line(self.world_surf, (255, 100, 100),
                             (cx-r, cy-r), (cx+r, cy+r), 2)
            pygame.draw.line(self.world_surf, (255, 100, 100),
                             (cx+r, cy-r), (cx-r, cy+r), 2)

        for (x, y) in self.world.obstacles:
            rect = pygame.Rect(x * cell, y * cell, cell, cell)
            pygame.draw.rect(self.world_surf, cfg.VISUAL.COLOR_OBSTACLE, rect)
            # Edge highlight
            pygame.draw.rect(self.world_surf, (70, 80, 100), rect, 1)

    def _draw_trails(self, agents: List[WorldAgent]):
        """Vẽ vết di chuyển của agent."""
        cell = self.cell
        for agent in agents:
            if len(agent.trail) < 2:
                continue
            n = len(agent.trail)
            for i, (tx, ty) in enumerate(agent.trail):
                alpha = int(180 * (i / n))
                radius = max(2, int(cell * 0.15 * (i / n)))
                surf = pygame.Surface((radius*2+1, radius*2+1), pygame.SRCALPHA)
                pygame.draw.circle(surf, (*agent.color, alpha),
                                   (radius, radius), radius)
                self.world_surf.blit(
                    surf,
                    (tx * cell + cell//2 - radius, ty * cell + cell//2 - radius)
                )

    def _draw_sensors(self, agents: List[WorldAgent]):
        """Vẽ sensor rays từ agent."""
        cell = self.cell
        for agent in agents:
            if not agent.is_alive:
                continue
            cx = agent.x * cell + cell // 2
            cy = agent.y * cell + cell // 2
            state = agent.get_state()[:24]   # Chỉ lấy sensor readings

            for i, (dx, dy) in enumerate(DIRECTIONS):
                # Lấy khoảng cách từ sensor
                min_dist = min(state[i*3], state[i*3+1], state[i*3+2])
                dist_px = int(min_dist * cfg.AGENT.sensor_range * cell)

                ex = cx + dx * dist_px
                ey = cy + dy * dist_px

                surf = pygame.Surface(
                    (abs(ex - cx) + 2, abs(ey - cy) + 2), pygame.SRCALPHA
                )
                color = (*agent.color, 25)
                pygame.draw.line(self.world_surf, color, (cx, cy), (ex, ey), 1)

    def _draw_agents(self, agents: List[WorldAgent]):
        """Vẽ agents với energy bar."""
        cell = self.cell
        for agent in agents:
            if not agent.is_alive:
                continue

            cx = agent.x * cell + cell // 2
            cy = agent.y * cell + cell // 2
            r = max(6, cell // 2 - 2)

            # Glow
            glow_r = r + 5
            glow_surf = pygame.Surface((glow_r*2, glow_r*2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*agent.color, 60),
                               (glow_r, glow_r), glow_r)
            self.world_surf.blit(glow_surf, (cx - glow_r, cy - glow_r))

            # Body
            pygame.draw.circle(self.world_surf, agent.color, (cx, cy), r)
            pygame.draw.circle(self.world_surf, (255, 255, 255), (cx, cy), r, 2)

            # ID label
            label = self.font_sm.render(str(agent.id), True, (255, 255, 255))
            self.world_surf.blit(label, (cx - label.get_width()//2,
                                         cy - label.get_height()//2))

            # Energy bar (bên trên agent)
            bar_w = cell
            bar_h = 4
            bx = agent.x * cell
            by = agent.y * cell - bar_h - 2
            pct = agent.energy_pct
            bg_rect = pygame.Rect(bx, by, bar_w, bar_h)
            fg_rect = pygame.Rect(bx, by, int(bar_w * pct), bar_h)

            pygame.draw.rect(self.world_surf, (50, 50, 70), bg_rect, border_radius=2)
            # Màu energy bar: xanh → vàng → đỏ
            if pct > 0.5:
                ec = (50, 200, 100)
            elif pct > 0.25:
                ec = (220, 180, 30)
            else:
                ec = (220, 60, 60)
            if fg_rect.width > 0:
                pygame.draw.rect(self.world_surf, ec, fg_rect, border_radius=2)

    # ─────────────────────────────────────────────────────────────────────────
    # HUD
    # ─────────────────────────────────────────────────────────────────────────

    def _draw_hud(self, agents: List[WorldAgent], paused: bool):
        """Vẽ HUD panel bên phải."""
        self.hud_surf.fill(cfg.VISUAL.COLOR_HUD_BG)
        pygame.draw.line(self.hud_surf, (40, 40, 80),
                         (0, 0), (0, self.hud_surf.get_height()), 2)

        from i18n import t

        y = 15
        pad = 14

        # Title
        title = self.font_lg.render(t("app_title"), True, (160, 130, 255))
        self.hud_surf.blit(title, (pad, y))
        y += 30

        # Episode
        ep_txt = self.font_md.render(f"{t('hud_episode')}: {self.episode}", True, (200, 200, 230))
        self.hud_surf.blit(ep_txt, (pad, y))
        y += 22

        # Step
        step_txt = self.font_sm.render(
            f"{t('hud_world_step')}: {self.world.step_count}  {t('hud_food')}: {len(self.world.foods)}",
            True, (150, 150, 180)
        )
        self.hud_surf.blit(step_txt, (pad, y))
        y += 20

        if paused:
            pause_txt = self.font_md.render(f"⏸ {t('hud_paused')}", True, (255, 200, 50))
            self.hud_surf.blit(pause_txt, (pad, y))
        y += 28

        # Divider
        pygame.draw.line(self.hud_surf, (40, 40, 80),
                         (pad, y), (HUD_WIDTH - pad, y), 1)
        y += 12

        # Agent panels
        header = self.font_sm.render("AGENTS", True, (120, 120, 160))
        self.hud_surf.blit(header, (pad, y))
        y += 18

        for agent in agents:
            y = self._draw_agent_panel(agent, y, pad)
            y += 8

        # Divider
        pygame.draw.line(self.hud_surf, (40, 40, 80),
                         (pad, y), (HUD_WIDTH - pad, y), 1)
        y += 12

        # Controls
        controls = [
            ("SPACE", "Pause/Resume"),
            ("S", "Toggle Sensors"),
            ("T", "Toggle Trails"),
            ("↑/↓", "Speed ±"),
            ("R", "Reset"),
            ("Q", "Quit"),
        ]
        ctrl_header = self.font_sm.render("CONTROLS", True, (120, 120, 160))
        self.hud_surf.blit(ctrl_header, (pad, y))
        y += 18

        for key, desc in controls:
            k_surf = self.font_sm.render(f"[{key}]", True, (160, 130, 255))
            d_surf = self.font_sm.render(desc, True, (180, 180, 210))
            self.hud_surf.blit(k_surf, (pad, y))
            self.hud_surf.blit(d_surf, (pad + 55, y))
            y += 16

    def _draw_agent_panel(self, agent: WorldAgent, y: int, pad: int) -> int:
        """Vẽ panel thông tin cho một agent."""
        info = agent.info
        panel_h = 80
        panel_rect = pygame.Rect(pad - 4, y - 4, HUD_WIDTH - pad*2 + 8, panel_h)

        # Background
        panel_surf = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        panel_surf.fill((*agent.color, 20))
        pygame.draw.rect(panel_surf, (*agent.color, 60),
                         (0, 0, panel_rect.width, panel_rect.height),
                         border_radius=6, width=1)
        self.hud_surf.blit(panel_surf, (panel_rect.x, panel_rect.y))

        # Status dot
        status_color = (50, 220, 100) if agent.is_alive else (200, 50, 50)
        pygame.draw.circle(self.hud_surf, status_color, (pad + 6, y + 8), 5)

        # Name
        name = f"Agent {agent.id} [{agent.agent_type.value}]"
        name_surf = self.font_sm.render(name, True, agent.color)
        self.hud_surf.blit(name_surf, (pad + 16, y + 1))
        y += 18

        # Energy bar
        bar_w = HUD_WIDTH - pad * 2 - 8
        bar_h = 6
        pct = agent.energy_pct
        bg_rect = pygame.Rect(pad, y, bar_w, bar_h)
        fg_rect = pygame.Rect(pad, y, int(bar_w * pct), bar_h)
        pygame.draw.rect(self.hud_surf, (40, 40, 60), bg_rect, border_radius=3)
        ec = (50, 200, 100) if pct > 0.5 else (220, 180, 30) if pct > 0.25 else (220, 60, 60)
        if fg_rect.width > 0:
            pygame.draw.rect(self.hud_surf, ec, fg_rect, border_radius=3)
        y += 10

        # Stats
        stats_line1 = f"⚡ {info['energy']:.0f}   🍎 {info['food_eaten']}   ε {info['epsilon']:.3f}"
        stats_line2 = f"Score: {info['score']:.0f}   Steps: {info['steps_alive']}"
        s1 = self.font_sm.render(stats_line1, True, (180, 180, 210))
        s2 = self.font_sm.render(stats_line2, True, (150, 150, 180))
        self.hud_surf.blit(s1, (pad, y))
        y += 14
        self.hud_surf.blit(s2, (pad, y))
        y += 14

        return y + 4

    # ─────────────────────────────────────────────────────────────────────────
    # UTILS
    # ─────────────────────────────────────────────────────────────────────────

    def handle_events(self) -> dict:
        """Xử lý keyboard events. Trả về dict các actions."""
        events = {"quit": False, "pause": False, "reset": False,
                  "speed_up": False, "speed_down": False,
                  "toggle_sensors": False, "toggle_trails": False}
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                events["quit"] = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    events["pause"] = True
                elif event.key == pygame.K_r:
                    events["reset"] = True
                elif event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                    events["quit"] = True
                elif event.key == pygame.K_UP:
                    events["speed_up"] = True
                elif event.key == pygame.K_DOWN:
                    events["speed_down"] = True
                elif event.key == pygame.K_s:
                    events["toggle_sensors"] = True
                elif event.key == pygame.K_t:
                    events["toggle_trails"] = True
        return events

    def quit(self):
        pygame.quit()
