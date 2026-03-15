/**
 * AKF Trust Metadata — Google Workspace Add-on
 *
 * Entry point: menu setup, sidebar, and Card Service homepage.
 */

function onOpen() {
  var ui;
  try {
    ui = DocumentApp.getUi();
  } catch (e) {
    try {
      ui = SpreadsheetApp.getUi();
    } catch (e2) {
      try {
        ui = SlidesApp.getUi();
      } catch (e3) {
        return;
      }
    }
  }

  ui.createMenu('AKF')
    .addItem('View Trust', 'showSidebar')
    .addItem('Run Audit', 'showAudit')
    .addItem('Run Detections', 'showDetections')
    .addItem('Embed Metadata', 'embedDefault')
    .addToUi();
}

function onInstall() {
  onOpen();
}

function onHomepage() {
  return buildHomepageCard();
}

function showSidebar() {
  var html = HtmlService.createHtmlOutputFromFile('Sidebar')
    .setTitle('AKF Trust Metadata')
    .setWidth(320);

  var ui;
  try {
    ui = DocumentApp.getUi();
  } catch (e) {
    try {
      ui = SpreadsheetApp.getUi();
    } catch (e2) {
      ui = SlidesApp.getUi();
    }
  }
  ui.showSidebar(html);
}

function showAudit() {
  var meta = getAKFMetadata();
  if (!meta) {
    var ui;
    try { ui = DocumentApp.getUi(); } catch (e) {
      try { ui = SpreadsheetApp.getUi(); } catch (e2) { ui = SlidesApp.getUi(); }
    }
    ui.alert('No AKF metadata found. Use "Embed Metadata" first.');
    return;
  }
  showSidebar();
}

function showDetections() {
  var meta = getAKFMetadata();
  if (!meta) {
    var ui;
    try { ui = DocumentApp.getUi(); } catch (e) {
      try { ui = SpreadsheetApp.getUi(); } catch (e2) { ui = SlidesApp.getUi(); }
    }
    ui.alert('No AKF metadata found. Use "Embed Metadata" first.');
    return;
  }
  showSidebar();
}

function embedDefault() {
  embedMetadata();
  showSidebar();
}
