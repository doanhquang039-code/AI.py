"""
core/algorithms.py — Các thuật toán tìm kiếm và sắp xếp truyền thống
"""
import heapq
from typing import List, Tuple, Callable, Any

def quick_sort(arr: List[Any], key: Callable[[Any], float] = lambda x: x) -> List[Any]:
    """
    Sắp xếp danh sách sử dụng thuật toán QuickSort.
    """
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    pivot_val = key(pivot)
    
    left = [x for x in arr if key(x) < pivot_val]
    middle = [x for x in arr if key(x) == pivot_val]
    right = [x for x in arr if key(x) > pivot_val]
    
    return quick_sort(left, key) + middle + quick_sort(right, key)


def manhattan_distance(p1: Tuple[int, int], p2: Tuple[int, int]) -> int:
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


def a_star_search(
    start: Tuple[int, int],
    target: Tuple[int, int],
    is_walkable: Callable[[int, int], bool],
    max_steps: int = 1000
) -> List[Tuple[int, int]]:
    """
    Thuật toán tìm đường A* (A-Star).
    Trả về danh sách các điểm (x, y) từ start đến target.
    Nếu không tìm được đường, trả về danh sách rỗng.
    """
    if not is_walkable(target[0], target[1]):
        return []

    # Priority Queue lưu trữ (f_score, count, current_node)
    open_set = []
    heapq.heappush(open_set, (0, 0, start))
    
    came_from = {}
    g_score = {start: 0}
    f_score = {start: manhattan_distance(start, target)}
    
    directions = [
        (-1, -1), (0, -1), (1, -1),
        (-1,  0),          (1,  0),
        (-1,  1), (0,  1), (1,  1)
    ]
    
    count = 1
    steps = 0
    
    while open_set and steps < max_steps:
        _, _, current = heapq.heappop(open_set)
        steps += 1
        
        if current == target:
            # Reconstruct path
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.reverse()
            return path
            
        x, y = current
        for dx, dy in directions:
            neighbor = (x + dx, y + dy)
            if not is_walkable(neighbor[0], neighbor[1]):
                continue
                
            # Khoảng cách giữa các node kề nhau là 1
            tentative_g_score = g_score[current] + 1
            
            if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f = tentative_g_score + manhattan_distance(neighbor, target)
                f_score[neighbor] = f
                heapq.heappush(open_set, (f, count, neighbor))
                count += 1
                
    return []
