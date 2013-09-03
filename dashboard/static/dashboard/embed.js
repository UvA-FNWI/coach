
function load_user(){
	// Set callback for when email is retrieved
	User.success_cb = function(){
		$('#lightbox').remove();
		$.get(
				"http://{{ host }}?email="+User.email,
				function(data){$('#coach_f').html(data)}
			 );
		document.getElementById('coach_f').src = "http://localhost:8000/bootstrap";
	}
	// init User object
	User.load();
}

var body = $('body', window.parent.document);
body.append('<div id="lightbox" style="position:absolute;top:0;left:0;background-color:rgba(0,0,0,.8);width:100%;height:100%;"></div>');
$('#lightbox').append('<div id="login" style="padding:30px;margin:0 auto;margin-top:100px;background-color:#FFF; width:500px; height:300px;"></div>')

$('#login').html("<h1>Lorem Ipsum</h1>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nam gravida, quam eget malesuada lobortis, orci dui pulvinar est, sed egestas augue ante ut nibh.<br />Mauris aliquam, mi at ultricies dapibus, elit ipsum sagittis velit, sit amet consectetur turpis nunc vitae magna. Proin lobortis elementum urna, eu malesuada eros luctus a.<br /><br />Pellentesque sed iaculis massa. Quisque pharetra dolor et dolor ornare condimentum. Sed venenatis risus quis orci commodo, sit amet ultricies justo fermentum. Sed vitae laoreet lectus. Donec semper odio vitae varius rutrum.");

$('#login').append('<div style="width:100%;text-align:center;margin-top:50px;"><button onclick="User.login()" type="button">Login</button></div>');

