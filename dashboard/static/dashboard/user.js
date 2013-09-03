/**
 * User object - created for COACH project
 *   Fetches the email adress using Google's OAuth2
 *
 * Usage:
 * <!DOCTYPE html>
 *  <html>
 *    <head><title>Demo</title></head>
 *	  <body>
 *		 <!-- load User object -->
 *		 <script src="user.js"></script>
 *		 <script type="text/javascript">
 *       // load function
 *		 function load_user(){
 *			 // Set callback for when email is retrieved
 *			 User.success_cb = function(){
 *			     alert("Hello "+User.email);
 *			 }
 *           // init User object
 *			 User.load();
 *		 }
 *		 </script>
 *		 <!-- load Google API client, onload parameter must contain the name
 *            of the load function defined above -->
 *		 <script src="https://apis.google.com/js/client.js?onload=load_user">
 *		 </script>
 *	  </body>
 *  </html>
 *
**/

// Google API clientID
var clientId = '794111581244-t1a11pubrv94atvtbil05gucr6cks775.apps.googleusercontent.com';
// Google API apiKey
var apiKey = 'AIzaSyCOIPbb0gPpbcjbJTvgMBKUuu_Jsi7eMbA';

// DO NOT EDIT BELOW THIS LINE, unless you want to.
var User = {
	email: undefined,
	scopes: 'https://www.googleapis.com/auth/userinfo.email',
	success_cb: function(){},
	error_cb: function(error){ alert("Error: "+error.message); },
	load: function(){
        gapi.client.setApiKey(apiKey);
        //window.setTimeout(User.login,0);
	},
	login: function(){
        gapi.auth.authorize(
			{
				client_id: clientId,
				scope: User.scopes,
				immediate: true,
			},
			User.handle_login
		);
	},
	handle_login: function( authResult ){
		if(authResult && !authResult.error){
			User.fetch()
		} else {
			gapi.auth.authorize(
				{
					client_id: clientId, 
					scope: User.scopes, 
					immediate: false,
					hd: "student.uva.nl"
				},
				User.handle_login
			);
		}
	},
	fetch: function(){
        gapi.client.load('oauth2', 'v2', function() {
			var request = gapi.client.oauth2.userinfo.get();
			request.execute(function(resp) {
				if(resp.email){
					User.email = resp.email
					User.success_cb()
				}else{
					User.error_cb(resp);
				}
			});
        });
	}
}
