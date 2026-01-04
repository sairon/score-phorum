(function() {
  'use strict';

  // Reply to message functionality
  document.querySelectorAll('.send-reply').forEach(function(button) {
    button.addEventListener('click', function() {
      var rootMessage = this.closest('.message');
      var recipientInput = document.getElementById('id_recipient');
      var threadInput = document.getElementById('id_thread');

      if (recipientInput && threadInput) {
        recipientInput.classList.add('reply');
        recipientInput.value = rootMessage.dataset.author;
        threadInput.value = rootMessage.dataset.threadId;
        window.scrollTo(0, 0);
        document.getElementById('id_text').focus();
      }
    });
  });

  // Clear thread when recipient changes
  var recipientInput = document.getElementById('id_recipient');
  var threadInput = document.getElementById('id_thread');
  if (recipientInput && threadInput) {
    recipientInput.addEventListener('input', function() {
      threadInput.value = '';
      this.classList.remove('reply');
    });
  }

  // Clear thread when switching to inbox
  var inboxCheckbox = document.getElementById('id_to_inbox');
  if (inboxCheckbox && threadInput) {
    inboxCheckbox.addEventListener('change', function() {
      threadInput.value = '';
      if (recipientInput) {
        recipientInput.classList.remove('reply');
      }
    });
  }

  // Confirm before deleting messages
  document.querySelectorAll('.delete-link a, .delete-link-mobile').forEach(function(link) {
    link.addEventListener('click', function(e) {
      if (!window.confirm('Opravdu chcete smazat příspěvek?')) {
        e.preventDefault();
        return;
      }
    });
  });

  // Jump to next unread message
  document.querySelectorAll('.jump-to-new').forEach(function(button) {
    button.addEventListener('click', function() {
      var message = this.closest('.message');
      var next = getNextSibling(message, '.new-message, .message:not(.reply)');
      if (next) {
        next.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  // Helper: find next sibling matching selector
  function getNextSibling(element, selector) {
    var sibling = element.nextElementSibling;
    while (sibling) {
      if (sibling.matches(selector)) {
        return sibling;
      }
      sibling = sibling.nextElementSibling;
    }
    return null;
  }

  // Smooth scroll to anchored post on page load
  if (window.location.hash) {
    var target = document.querySelector(window.location.hash);
    if (target) {
      setTimeout(function() {
        var targetPosition = target.getBoundingClientRect().top + window.pageYOffset - 20;
        window.scrollTo({ top: targetPosition, behavior: 'smooth' });
      }, 100);
    }
  }
})();
