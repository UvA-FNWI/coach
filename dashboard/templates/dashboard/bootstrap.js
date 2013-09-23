var container = document.getElementById("coach");
{% if width > 0 %}
var width = {{ width|safe|escape }};
{% else %}
var width = (container ? container.offsetWidth : 300)
{% endif %}
container = (container ? container : document.body)
var frame = document.createElement("iframe");
frame.setAttribute("style","border: 0px;");
frame.height = window.screen.availHeight;
frame.width = width;
var search = (location.search.length > 2 ? location.search+"&" : "?" );
frame.src = "http://{{ host }}/"+search+"width="+(width-30);
container.appendChild(frame);
