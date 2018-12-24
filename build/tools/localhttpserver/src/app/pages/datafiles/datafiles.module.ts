import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { DatafilesRoutingModule } from './datafiles-routing.module';
import { FileListComponent } from './file-list.component';

@NgModule({
  declarations: [FileListComponent],
  imports: [
    CommonModule,
    DatafilesRoutingModule
  ]
})
export class DatafilesModule { }
