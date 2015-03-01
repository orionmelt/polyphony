var p = polyphony;

function onYouTubeIframeAPIReady() {
  p.youtube_ready();
}

$(function () {
  var data_sources = JSON.parse(localStorage.getItem("data_sources"));

  if(data_sources) {
    $("input[name*='data_source']").prop("checked",false);
    data_sources.forEach(function(d) {
      $("#"+d).prop("checked",true);
    });
    p.set_data_sources(data_sources);
  }


  $.ajax("/playlist" + (data_sources ? "?data_sources="+data_sources.join(",") : "")).done(function(data) {
    p.initialize({
      playlist:data.playlist,
      data_sources:data_sources
    });
    p.refresh_playlist();
    $("#playlist").scrollTo($("#track0"));
  });

  
  $(window).on("keydown", function(event) {
    if(event.type==="keydown" && event.which===32) { //Spacebar
      event.preventDefault();
      $("#stp-play").trigger("click");
    }

    if(event.type==="keydown" && event.which===65) { //A
      $("#stp-prev").trigger("click");
    }

    if(event.type==="keydown" && event.which===68) { //D
      $("#stp-next").trigger("click");
    }
  });
  

  $(".track-container").click(function(e) {
    e.preventDefault();
    var track_number = $(this).data("track-number");
    p.play(track_number,true);
  });

  setTimeout(function() {
    p.update_playlist();
  }, 1800000);

  $("#source-prefs-form").submit(function(event) {
    event.preventDefault();
    $("#source-prefs-submit").button("loading");
    var form_data = $(this).serializeArray();
    localStorage.setItem("data_sources",JSON.stringify(form_data.map(function (d) {
      return d.value;
    })));
    var data_sources = JSON.parse(localStorage.getItem("data_sources"));
    $.ajax("/playlist" + (data_sources ? "?data_sources="+data_sources.join(",") : "")).done(function(data) {
      p.set_playlist(data.playlist);
      p.set_data_sources(data_sources);
      p.refresh_playlist();
      $("#playlist").scrollTo($("#track0"));
      $("#source-prefs-submit").button("reset");
    });
    
  });
});


