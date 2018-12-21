import { Component, OnInit, OnDestroy } from '@angular/core';
import { FormControl } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';

import { Observable, Subject, Subscription } from 'rxjs';
import { map } from 'rxjs/operators';

import { ModulesService, IModuleInfo } from './modules.service';
import { MatDialog, MatDialogRef, MatAutocompleteSelectedEvent } from '@angular/material';
import { LoadingDialogComponent } from './loading-dialog/loading-dialog.component';

@Component({
  selector: 'app-modules',
  templateUrl: './modules.component.html',
  styleUrls: ['./modules.component.scss']
})
export class ModulesComponent implements OnInit, OnDestroy {

  myControl = new FormControl();
  filteredModulesInfo: Observable<IModuleInfo[]>;

  private showDialogTimeoutId;
  private loadingDialogRef: MatDialogRef<LoadingDialogComponent>;
  private subscriptionForValueChanges: Subscription;
  private filterSubject: Subject<string> = new Subject<string>();
  private delayAutocompleteFilterTimeout = undefined;

  constructor(
    private dialog: MatDialog,
    private modulesSrv: ModulesService,
    private router: Router,
    private route: ActivatedRoute,
  ) { }

  ngOnInit() {
    this.showDialogTimeoutId = setTimeout(this.showLoadingDataDialog.bind(this), 500);
    this.modulesSrv.loadDataFile().subscribe(result => {
      clearTimeout(this.showDialogTimeoutId);
      this.showDialogTimeoutId = undefined;
      if (this.loadingDialogRef) {
        this.loadingDialogRef.close();
      }
    });
    this.subscriptionForValueChanges = this.myControl.valueChanges.subscribe(value => {
      if (this.delayAutocompleteFilterTimeout) {
        clearTimeout(this.delayAutocompleteFilterTimeout);
        this.delayAutocompleteFilterTimeout = undefined;
      }
      return this.filterSubject.next(value);
    });
    this.filteredModulesInfo = this.filterSubject.pipe(
      map(value => {
        let forceFilter = false;
        // Magic prefix.
        if (typeof (value) === 'string' && value.startsWith('***')) {
          forceFilter = true;
          value = value.substr(3);
        }
        return this._filter(value, forceFilter);
      }),
    );
  }

  ngOnDestroy() {
    this.subscriptionForValueChanges.unsubscribe();
  }

  displayFn(moduleInfo?: IModuleInfo): string | undefined {
    return moduleInfo ? moduleInfo.key : undefined;
  }

  moduleSelected(event: MatAutocompleteSelectedEvent) {
    const moduleInfo = event.option.value;
    // TODO: navigate to module detail page.
    this.router.navigate(['detail', moduleInfo.key], { relativeTo: this.route });
  }

  private showLoadingDataDialog() {
    this.loadingDialogRef = this.dialog.open(LoadingDialogComponent, {
      disableClose: true,
    });
  }

  private _filter(value: string, forceFilter: boolean = false): IModuleInfo[] {
    let results = [];
    let subModulesInfo = [];
    if (typeof (value) === 'string') {
      const filterValue = value.toLocaleLowerCase();
      if (filterValue.length > 1) {
        const firstTwoChars = filterValue.substr(0, 2);
        subModulesInfo = this.modulesSrv.getSubModulesInfo(firstTwoChars);
      } else {
        const firstChar = filterValue[0];
        subModulesInfo = this.modulesSrv.getSubModulesInfo(firstChar);
        // Large size of data set will cause performance issue, so return empty
        // data set and let user enter more chars for further filtering.
        if (subModulesInfo.length > 5000 && !forceFilter) {
          subModulesInfo = [];
          this.delayAutocompleteFilterTimeout = setTimeout(() => {
            this.filterSubject.next('***' + filterValue);
          }, 1000);
        }
      }
      results = subModulesInfo.filter(info => info.module_name.toLocaleLowerCase().includes(filterValue));
    }
    return results;
  }

}
