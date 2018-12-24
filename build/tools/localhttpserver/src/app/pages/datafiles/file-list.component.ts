import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-file-list',
  templateUrl: './file-list.component.html',
  styleUrls: ['./file-list.component.scss']
})
export class FileListComponent implements OnInit {

  dataFiles = [
    'product-info.json',
    'module-info.json',
    'module-deps.json',
  ];

  constructor() { }

  ngOnInit() {
  }

}
