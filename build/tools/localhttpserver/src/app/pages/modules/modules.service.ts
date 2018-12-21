import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { map, catchError } from 'rxjs/operators';

export interface IModuleInfo {
  module_name: string;
  key: string;
  class: string[];
  path: string[];
  tags: string[];
  installed: string[];
  compatibility_suites: string[];
  auto_test_config: boolean[];
  test_config: string[];
  dependencies: string[];
  srcs: string[];
}

export interface IModulesInfo {
  [key: string]: IModuleInfo;
}

@Injectable({
  providedIn: 'root'
})
export class ModulesService {

  // Origin modules info data.
  modulesInfo: IModulesInfo;

  // Indexed modules info data.
  private indexForModulesInfo: Map<string, IModuleInfo[]> = new Map<string, IModuleInfo[]>();

  constructor(private http: HttpClient) { }

  public loadDataFile(): Observable<boolean> {
    if (this.modulesInfo) {
      return of(true);
    }
    return this.http.get('assets/module-info.json').pipe(
      map(resp => {
        this.modulesInfo = resp as IModulesInfo;
        this.preprocessData();
        return true;
      }),
      catchError(err => of(false))
    );
  }

  public getSubModulesInfo(index: string): IModuleInfo[] {
    const data: IModuleInfo[] = [];
    if (index && this.modulesInfo && this.indexForModulesInfo.has(index.toLocaleLowerCase())) {
      return this.indexForModulesInfo.get(index);
    }
    return data;
  }

  private preprocessData() {
    // Generate map to accelerate access of group of module info.
    for (const key in this.modulesInfo) {
      if (this.modulesInfo.hasOwnProperty(key)) {
        const moduleInfo = this.modulesInfo[key];
        moduleInfo.key = key;

        // Indexes modules info for accelerating access module info.
        const firstChar = moduleInfo.module_name[0].toLocaleLowerCase();
        if (!this.indexForModulesInfo.has(firstChar)) {
          this.indexForModulesInfo.set(firstChar, []);
        }
        this.indexForModulesInfo.get(firstChar).push(moduleInfo);

        if (moduleInfo.module_name.length > 1) {
          const firstTwoChars = moduleInfo.module_name.substr(0, 2).toLocaleLowerCase();
          if (!this.indexForModulesInfo.has(firstTwoChars)) {
            this.indexForModulesInfo.set(firstTwoChars, []);
          }
          this.indexForModulesInfo.get(firstTwoChars).push(moduleInfo);
        }
      }
    }
  }

}
