(function(Uploader, $) {
// Private Property
  let currentTableName;
  let editor;
  const baseApiPath = 'upload-filelist';

  // Public Property

  Uploader.editorFilters = undefined;
  Uploader.filelistApiResponse = undefined;
  Uploader.newOrderingApiResponse = undefined;
  Uploader.assignFilenameSelected = undefined;
  Uploader.presetDocType = undefined;

  Uploader.storeSelectedRow = function storeSelectedRow(rowId, mainFieldValue) {
    // console.log('Uploader.storeSelectedRow rowId=', rowId, mainFieldValue); // example: rowId= 1 NAS-Mem.txt
    Uploader.lastSelectedMainCellText = mainFieldValue;
    Uploader.lastSelectedRowId = rowId;
  };

  Uploader.onRemoveClicked = function onRemoveClicked(actionDefs, rowId) {
    for (const fileRowIndex in Uploader.filelistApiResponse.data) {
      if (Object.prototype.hasOwnProperty.call(Uploader.filelistApiResponse.data, fileRowIndex)) {
        // this "if" is requested by the eslint rule guard-for-in
        const fileRow = Uploader.filelistApiResponse.data[fileRowIndex];
        if (fileRow.DT_RowId.toString() === Uploader.lastSelectedRowId) {
          $('#modal-confirm-title').text('Confirm Action');
          $('#modal-confirm-body').text(`Do you really want to delete the uploaded file ${fileRow.filename}?`);
          $('#modal-confirm-ok').click(function() {
            $.ajax({
              url: `${TableUtils.apiPath}/upload?${$.param({ id: rowId, file: fileRow.filename })}`,
              type: 'DELETE',
              success: function(result) { // eslint-disable-line no-unused-vars
                // Do something with the result
                let table = $('#upload-dir-table').DataTable();
                table.ajax.reload();
              }
            });
          });
          $('#modalConfirmAction').modal();
          break;
        }
      }
    }
  };

  // Public Method
  Uploader.create = function create(tableName, resourceViewSpec, containerSelector) {
    currentTableName = 'documents';

    const container1 = '<div id="main-container">';
    const header1 = `<h1 id="main_title">${Lang.t('doc_upload.upload_tool')}</h1>`;
    const content1 = `<form action="${TableUtils.apiPath}/upload" class="dropzone" id="docupload" \
                     style="margin-bottom:15px"></form>`;
    const header2 = `<h1 id="main_title">${Lang.t('doc_upload.upload_pool')}</h1>`;
    const content2 = '<table id="upload-dir-table" class="display" cellspacing="0" width="100%"></table>';
    const container2 = '</div>';

    const htmlstr = container1 + header1 + content1 + header2 + content2 + container2;
    $(containerSelector).replaceWith(htmlstr);
    Uploader.queryEditorSpec();
  };

  // --- 1. query the spec for getting the filters ---

  Uploader.queryEditorSpec = function queryEditorSpec() {
    TableUtils.apiRequest(baseApiPath, undefined, undefined, false, true)
      .done(function(apiResponseSource) {
        Uploader.editorFilters = apiResponseSource['editor-filters'];
        console.log('(1) Upload editor filters:', Uploader.editorFilters);
        Uploader.queryFileList();
      }
      );
  };

  // --- 2. query the data for getting the options in the standalone editor ---

  Uploader.queryFileList = function queryFileList() {
  // here, we have already the available filters stored; user the default filter to query the standalone editor options
    const currentEditorFilter = TableUtils.generateEditorFilterDefaults(baseApiPath, Uploader.editorFilters);

    TableUtils.apiRequest(baseApiPath, undefined, currentEditorFilter, true, false)
      .done(function(apiResponseSource) {
        Uploader.filelistApiResponse = apiResponseSource;
        console.log('(2) Upload area filelist:', currentTableName, 'response:', Uploader.filelistApiResponse);
        Uploader.filelistApiRequestDone();
      }
      );
  };

  // eslint-disable-next-line no-unused-vars
  Uploader.onDocInitCreate = function onDocInitCreate(e) {
    editor = this;
    for (const fileRowIndex in Uploader.filelistApiResponse.data) {
      if (Object.prototype.hasOwnProperty.call(Uploader.filelistApiResponse.data, fileRowIndex)) {
        // this "if" is requested by the eslint rule guard-for-in
        const fileRow = Uploader.filelistApiResponse.data[fileRowIndex];
        if (fileRow.DT_RowId.toString() === Uploader.lastSelectedRowId) {
          editor.field('documents.filename').set(fileRow.filename);
          editor.field('documents.name').set(fileRow.name);
          editor.field('documents.filedate').set(fileRow.filedate);
          break;
        }
      }
    }
  };

  Uploader.filelistApiRequestDone = function filelistApiRequestDone() {
    console.log('Upload resource spec (2):', Uploader.filelistApiResponse);

    // prepare standalone editor parameters
    let editorParam = {
      tableName: 'documents',
      apiEditorSpec: Uploader.filelistApiResponse, // this contains edit fields for new documents
      editorFilterSpec: Uploader.editorFilters,
      currentEditorFilter: TableUtils.generateEditorFilterDefaults(baseApiPath, Uploader.editorFilters),
      onInitCreate: Uploader.onDocInitCreate,
      onInitEdit: null,
      onInitDelete: null,
      onSubmitSuccess: function(e) { // eslint-disable-line no-unused-vars
        $('#upload-dir-table').DataTable().ajax.reload();
      }
    };
    // do not call the editor here, but on button action (StandaloneEditor.open(editorParam))

    // upload file table: change the link column
    let linkIndex = -1;
    let indexCnt = 0;
    for (const columnno in Uploader.filelistApiResponse['table-fields']) {
      // console.log(Uploader.filelistApiResponse['table-fields'][columnno]);

      if (Object.prototype.hasOwnProperty.call(Uploader.filelistApiResponse['table-fields'], columnno)) {
        // this "if" is requested by the eslint rule guard-for-in

        if (Uploader.filelistApiResponse['table-fields'][columnno].data === 'name') {
        // eslint-disable-next-line no-unused-vars
          Uploader.filelistApiResponse['table-fields'][columnno].render = function (data, type, row, meta) {
            return `<a href="${row.link}">${data}</a>`;
          };
        }
        if (Uploader.filelistApiResponse['table-fields'][columnno].data === 'link') {
          linkIndex = indexCnt;
        // Uploader.filelistApiResponse['table-fields'][columnno].render = function (data, type, row, meta) {
        //    console.log('link column:', data, ' in row:', row, meta);
        //    return '<a href="' + data + '">' + data + '</a>';
        // }
        }
        indexCnt += 1;
      }
    }
    // remove the 'link' column because it is used in the link of the column 'name'
    if (linkIndex >= 0) {
      Uploader.filelistApiResponse['table-fields'].splice(linkIndex, 1);
    }
    // console.log(Uploader.filelistApiResponse['table-fields']);

    TableUtils.add_actions('#upload-dir-table', Uploader.filelistApiResponse['table-fields'], editorParam, {
      add: { icon: 'images/action-assign-white.svg', title: 'Datei % im Archiv speichern', buttonText: 'Zuweisen',
        linkHint: 'Datei im Archiv speichern' },
      remove: { icon: 'images/action-delete-white.svg', title: 'Datei im Upload löschen', buttonText: 'Löschen',
        message: 'Willst du % wirklich löschen?', linkHint: 'Datei im Upload löschen',
        action: Uploader.onRemoveClicked }
    }, 'name', Uploader.storeSelectedRow);
    // console.log('Uploader table-fields', Uploader.filelistApiResponse['table-fields']);

    // --- 3. query the data for getting the files (= table data);
    //        editor fields are unused because of the standalone editor ---

    $('#upload-dir-table').dataTable({
      destroy: true,
      responsive: true,
      dom: 'Bfrtip',
      ajax: TableUtils.generateAjaxConfig('upload-filelist', { editor_filter: editorParam.currentEditorFilter }),
      columns: Uploader.filelistApiResponse['table-fields'],
      select: true,
      pageLength: 100,
      columnDefs: [{
        targets: [0],
        className: 'no-wrap',
        // width: "300px",
        orderable: false
      }],
      language: {
        url: Lang.t('datatables_language_url')
      }
      // note: use inline buttons instead
      // buttons: [
      //    { extend: "create", editor: editorDirTable },
      //    { extend: "edit",   editor: editorDirTable },
      //    { extend: "remove", editor: editorDirTable }
      // ]
    });

    $('#docupload').dropzone({
      url: `${TableUtils.apiPath}/upload`,
      paramName: 'file', // The name that will be used to transfer the file,
      maxFilesize: 250, // MB
      uploadMultiple: true,
      success: function(file, response) {
        console.log(`File upload completed (direct): ${file.name}`);
        console.log(response);
        Uploader.reload();
      },
      error: function(file, response) {
        console.error(`File upload error (direct): ${file.name}`);
        console.log(response);
      }
    });
  };

  Uploader.reload = function reload() {
    Uploader.queryEditorSpec();

    let uploadDirTable = $('#upload-dir-table').DataTable();
    // console.log('reloading upload-dir-table');
    uploadDirTable.ajax.reload(function () {
      uploadDirTable.draw(false);
    });
  };
}(window.Uploader = window.Uploader || {}, jQuery));
