(function(document, window, $) {
  $('.send-reply').click(function(e) {
    var rootMessage = $(this).closest('.message');
    var recipientInput = $('#id_recipient'),
      threadInput = $('#id_thread');
    if (recipientInput) {
      recipientInput.addClass("reply");
      recipientInput.val(rootMessage.data('author'));
      threadInput.val(rootMessage.data('thread-id'));
      window.scrollTo(0, 0);
      $('#id_text').focus();
    }
  });

  $('#id_recipient').on('change paste input', function(e) {
    $("#id_thread").val("");
    $("#id_recipient").removeClass("reply");
  });

  $('#id_to_inbox').on('change', function(e) {
    $("#id_thread").val("");
    $("#id_recipient").removeClass("reply");
  });
})(document, window, jQuery);
