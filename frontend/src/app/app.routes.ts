import { Routes } from '@angular/router';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { TrainingComponent } from './components/training/training.component';
import { VisualizationComponent } from './components/visualization/visualization.component';
import { ComparisonComponent } from './components/comparison/comparison.component';
import { ExportImportComponent } from './components/export-import/export-import.component';
import { IoTAiComponent } from './components/iot-ai/iot-ai.component';
import { ProjectHubComponent } from './components/project-hub/project-hub.component';
import { BiometricAiComponent } from './components/biometric-ai/biometric-ai.component';
import { AiCopilotComponent } from './components/ai-copilot/ai-copilot.component';
import { DataAnalyticsAiComponent } from './components/data-analytics-ai/data-analytics-ai.component';

export const routes: Routes = [
  { path: '', component: DashboardComponent },
  { path: 'copilot', component: AiCopilotComponent },
  { path: 'data-analytics', component: DataAnalyticsAiComponent },
  { path: 'projects', component: ProjectHubComponent },
  { path: 'dashboard', component: DashboardComponent },
  { path: 'training', component: TrainingComponent },
  { path: 'visualization', component: VisualizationComponent },
  { path: 'comparison', component: ComparisonComponent },
  { path: 'iot-ai', component: IoTAiComponent },
  { path: 'biometric-ai', component: BiometricAiComponent },
  { path: 'export-import', component: ExportImportComponent },
  { path: '**', redirectTo: '' }
];
