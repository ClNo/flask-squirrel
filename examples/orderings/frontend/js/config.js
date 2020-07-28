(function(Config, $) {
  let configApiResponse;

  Config.create = function create(containerSelector) {
    let content = '<div id="main-container"><div class="container"><div id="main-alert"/>';
    content += `<h1>${Lang.t('config.title')}</h1>`;
    content += `<label for="ordering-counter-inp">${Lang.t('config.next_order_number')}`;
    content += '<input type="number" class="form-control config-top-spacer" id="ordering-counter-inp" />';
    content += '<button type="button" class="btn btn-primary config-top-spacer" ';
    content += `id="ordering-counter-submit">${Lang.t('config.save_button')}</button>`;
    content += '</label>';
    content += '</div></div>';

    $(containerSelector).replaceWith(content);

    TableUtils.apiRequest('config-api', undefined, undefined, true, false)
      .done(function(apiResponse) {
        configApiResponse = apiResponse;
        console.log('Config received:', configApiResponse);
        $('#ordering-counter-inp').val(configApiResponse.data.ordering_counter);
      });

    $('#ordering-counter-submit').click(function (e) {
      e.preventDefault();

      const orderingCounter = $('#ordering-counter-inp').val();
      if (orderingCounter === undefined) {
        console.log('Error: input field is invalid! #ordering-counter-inp');
        return;
      }
      if (orderingCounter.length === 0) {
        console.log('Error: input filed is invalid! #ordering-counter-inp');
        return;
      }

      let ajaxData = TableUtils.generateAjaxConfig('config-api', { ordering_counter: orderingCounter });
      ajaxData.type = 'PUT';
      ajaxData.contentType = 'application/json';
      ajaxData.dataType = 'json';
      delete ajaxData.get; // it's not a GET request so this field is not used
      ajaxData.data = JSON.stringify(ajaxData.data);
      $.ajax(ajaxData)
        .fail(function (xhr, ajaxOptions, thrownError) {
          const placeholders = { SERVER_ERROR: thrownError };
          const innerHtml = Lang.t('config.error_save', placeholders);
          $('#main-alert').addClass('alert alert-warning').attr('role', 'alert').html(innerHtml);
          console.error(innerHtml);

          if (configApiResponse && configApiResponse.data) {
            $('#ordering-counter-inp').val(configApiResponse.data.ordering_counter);
          }
        });
    });
  };
}(window.Config = window.Config || {}, jQuery));
