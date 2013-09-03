
function load_user(){
	// Set callback for when email is retrieved
	User.success_cb = function(){
		$('#lightbox').remove();
		document.getElementById('coach_f').src = "http://localhost:8000/bootstrap";
	}
	// init User object
	User.load();
	window.setTimeout(function(){User.login(User.try_login);},5);
}

var body = $('body', window.parent.document);
body.append('<div id="lightbox" style="position:fixed;top:0;left:0;background-color:rgba(0,0,0,.8);width:100%;height:100%;"></div>');
$('#lightbox').append('<div id="login" style="position: relative; padding:30px;margin:0 auto;margin-top:100px;background-color:#FFF; width:500px; height:380px;"></div>')

$('#login').html("<h1>Inloggen</h1>Om gebruik te kunnen maken van de functionaliteit op deze pagina moet je eerst inloggen. Dat doe je door op de onderstaande knop te klikken. Je logt in met je UvANetId en wachtwoord (hetzelfde als voor Blackboard).<br /><br />De allereerste keer dat je inlogt zal Google je vragen om toestemming te geven aan <b>UvA ICTO-FNWI COACH</b> om je UvA email adres in te zien. We gebruiken dat email adres alleen voor het opbouwen van deze cursus website. We hebben geen toegang tot je emails of andere content binnen Google producten. Heb je hier vragen over? Ga dan langs bij de docent van dit vak.<br /><br /><b>LET OP:</b><br />Het zou kunnen dat je browser een popup-blocker heeft. Als er geen inlogscherm verschijnt nadat je op de inlog knop hebt geklikt, dan zou het kunnen dat deze popup-blocker het inlogscherm tegen gehouden heeft. Zorg dan dat je deze website toestaat popup schermen te maken. Zie <a href=\"https://support.google.com/chrome/answer/95472?hl=nl\">deze pagina</a> voor uitleg hoe je dat moet doen in de Google Chrome browser. Zie <a href=\"https://support.mozilla.org/en-US/kb/pop-blocker-settings-exceptions-troubleshooting\">deze pagina</a> voor uitleg voor de Mozilla Firefox browser. En zie <a href=\"http://windows.microsoft.com/nl-nl/internet-explorer/ie-security-privacy-settings#ie=ie-10\">deze pagina</a> voor uitleg als je de Microsoft Internet Explorer browser hebt.");
$('#login').append('<img style="position: absolute; top: 10px; left: 10px; width: 200px;" src="http://www.uva.nl/gfx/logo.png" />');
$('#login').append('<div style="width:100%;text-align:center;margin-top:20px;"><button onclick="User.login()" type="button">Login met UvANetID</button></div>');
