import { Routes } from '@angular/router';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { TrainingComponent } from './components/training/training.component';
import { VisualizationComponent } from './components/visualization/visualization.component';
import { ComparisonComponent } from './components/comparison/comparison.component';
import { ExportImportComponent } from './components/export-import/export-import.component';

export const routes: Routes = [
  { path: '', component: DashboardComponent },
  { path: 'dashboard', component: DashboardComponent },
  { path: 'training', component: TrainingComponent },
  { path: 'visualization', component: VisualizationComponent },
  { path: 'comparison', component: ComparisonComponent },
  { path: 'export-import', component: ExportImportComponent },
  { path: '**', redirectTo: '' }
];
