(function(document, window, $) {
  $('.send-reply').click(function(e) {
    var rootMessage = $(this).closest('.message');
    var recipientInput = $('#id_recipient'),
      threadInput = $('#id_thread');
    if (recipientInput) {
      recipientInput.val(rootMessage.data('author'));
      threadInput.val(rootMessage.data('thread-id'));
      window.scrollTo(0, 0);
      $('#id_text').focus();
    }
  });

  $('#id_recipient').on('change paste input', function(e) {
    $("#id_thread").val("");
  });
})(document, window, jQuery);
