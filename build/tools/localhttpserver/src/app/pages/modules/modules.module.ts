import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { CovalentJsonFormatterModule } from '@covalent/core/json-formatter';

import { ModulesRoutingModule } from './modules-routing.module';
import { ModulesComponent } from './modules.component';
import { ModuleDetailComponent } from './module-detail/module-detail.component';
import { ModulesService } from './modules.service';
import { LoadingDialogComponent } from './loading-dialog/loading-dialog.component';

@NgModule({
  declarations: [ModulesComponent, ModuleDetailComponent, LoadingDialogComponent],
  imports: [
    CommonModule,
    HttpClientModule,
    FormsModule,
    ReactiveFormsModule,
    CovalentJsonFormatterModule,
    MatAutocompleteModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatProgressSpinnerModule,
    ModulesRoutingModule
  ],
  entryComponents: [LoadingDialogComponent],
  providers: [ModulesService]
})
export class ModulesModule { }
