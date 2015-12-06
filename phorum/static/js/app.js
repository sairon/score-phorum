if (!Element.prototype.hasClass) {
  Element.prototype.hasClass = function(className) {
    return new RegExp('(^| )' + className + '( |$)', 'gi').test(this.className);
  }
}

Element.prototype.firstAncestorOfClass = function(className) {
  var el = this;
  while ((el = el.parentElement) && !el.hasClass(className)) {}
  return el;
};

var replyEls = document.querySelectorAll(".send-reply");

Array.prototype.forEach.call(replyEls, function(el, i) {
  el.addEventListener('click', function(e) {
    var rootMessage = el.firstAncestorOfClass('message');

    var recipientInput = document.getElementById("id_recipient");
    if (recipientInput) {
      recipientInput.value = rootMessage.getAttribute('data-author');
      document.getElementById("id_thread").value = rootMessage.getAttribute('data-thread-id');
      window.scrollTo(0, 0);
      document.getElementById("id_text").focus();
    }
  });
});
