import { Component, OnInit } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';

import { ModulesService, IModuleInfo } from '../modules.service';

@Component({
  selector: 'app-module-detail',
  templateUrl: './module-detail.component.html',
  styleUrls: ['./module-detail.component.scss']
})
export class ModuleDetailComponent implements OnInit {

  moduleInfo: IModuleInfo;
  dependencyTreeConfig = {};

  private baseConfig = {
    'grid': {
      'borderColor': 'transparent'
    },
    'xAxis': {
      'show': false
    },
    'yAxis': {
      'show': false
    },
    'tooltip': {
      'trigger': 'item',
      'triggerOn': 'mousemove'
    },
    'series': [
      {
        'type': 'tree',
        'top': '12%',
        'left': '2%',
        'bottom': '25%',
        'right': '2%',
        'orient': 'vertical',
        'expandAndCollapse': false,
        'itemStyle': {
          'borderColor': '#F2724B',
          'color': '#F2724B'
        },
        'label': {
          'distance': 5,
          'position': 'top',
          'fontSize': 18,
          'backgroundColor': '#3A4950',
          'color': 'white',
          'padding': [2.5, 5],
          'borderRadius': 10,
        },
        'leaves': {
          'label': {
            'distance': 5,
            'fontSize': 10,
            'position': 'bottom',
            'backgroundColor': '#3A4950',
            'color': 'white',
            'padding': [2.5, 5],
            'borderRadius': 10,
            'rotate': -90,
            'verticalAlign': 'middle',
            'align': 'left',
          }
        },
        'animationDuration': 550,
        'animationDurationUpdate': 750,
        'data': [],
      }
    ],
  };

  constructor(
    private router: Router,
    private route: ActivatedRoute,
    private moduleSrv: ModulesService,
  ) { }

  ngOnInit() {
    this.route.paramMap.subscribe(params => {
      const moduleKey = params.get('key');
      if (moduleKey in this.moduleSrv.modulesInfo) {
        this.moduleInfo = this.moduleSrv.modulesInfo[moduleKey];
        this.dependencyTreeConfig = this.buildDirectDependencyTreeConfig();
      }
    });
  }

  onChartClick($event) {
    this.router.navigate(['../', $event.name], { relativeTo: this.route });
  }

  private buildDirectDependencyTreeConfig(): any {
    const config = Object.assign({}, this.baseConfig);
    const treeData = {
      'name': this.moduleInfo.module_name,
      'children': []
    };
    this.moduleInfo.dependencies.forEach(dependency => {
      treeData.children.push({
        name: dependency
      });
    });
    if (this.moduleInfo.dependencies.length === 0) {
      config.series[0].leaves.label.rotate = 0;
      config.series[0].leaves.label.fontSize = 18;
      config.series[0].leaves.label.align = 'center';
      config.series[0].leaves.label.distance = 16;
    } else {
      config.series[0].leaves.label.rotate = -90;
      config.series[0].leaves.label.fontSize = 10;
      config.series[0].leaves.label.align = 'left';
      config.series[0].leaves.label.distance = 15;
    }
    config.series[0].data = [treeData];
    return config;
  }

}
