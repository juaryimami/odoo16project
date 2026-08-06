(function () {
    if (document.getElementById("footer")) {
        return;
    }
    const qq = document.createElement("div");
    qq.id = "footer";
    const p = document.getElementsByClassName("o_web_client");
    if (p && p.length > 0) {
        p[0].appendChild(qq);
        qq.innerHTML += "<p> &copy; COPY RIGHT 2026 NEMAL ENGINEERING P.L.C ALL RIGHT RESERVED </p>";
    }
})();