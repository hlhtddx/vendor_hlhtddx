import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';

import { ModulesService, IModuleInfo } from '../modules.service';

@Component({
  selector: 'app-module-detail',
  templateUrl: './module-detail.component.html',
  styleUrls: ['./module-detail.component.scss']
})
export class ModuleDetailComponent implements OnInit {

  moduleInfo: IModuleInfo;

  constructor(
    private route: ActivatedRoute,
    private moduleSrv: ModulesService,
  ) { }

  ngOnInit() {
    this.route.paramMap.subscribe(params => {
      const moduleKey = params.get('key');
      if (moduleKey in this.moduleSrv.modulesInfo) {
        this.moduleInfo = this.moduleSrv.modulesInfo[moduleKey];
      }
    });
  }

}
