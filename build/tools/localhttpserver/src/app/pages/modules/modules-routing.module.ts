import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

import { ModulesComponent } from './modules.component';
import { ModuleDetailComponent } from './module-detail/module-detail.component';

const routes: Routes = [
  {
    path: 'modules',
    component: ModulesComponent,
    children: [
      { path: 'detail/:key', component: ModuleDetailComponent },
    ],
  },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class ModulesRoutingModule { }
