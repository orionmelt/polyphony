!function(){
  var polyphony={version:"0.1"};

  var PLAYING=1, PAUSED=2, STOPPED=-1, UNDEFINED=-2;
  var players= ["youtube", "soundcloud"];
  var players_loaded = [],
      playlist = [],
      data_sources = [],
      current_track = -1,
      youtube_player = null,
      soundcloud_player = null,
      current_player = null,
      player_state = UNDEFINED;

  var play_button, prev_button, next_button;

  polyphony.initialize = function(options) {
    playlist = options.playlist || [];
    data_sources = options.data_sources || [];
    play_button = $("#" + (options.play_button || "stp-play"));
    prev_button = $("#" + (options.prev_button || "stp-prev"));
    next_button = $("#" + (options.prev_button || "stp-next"));

    var that = this;

    players.forEach(function(d) {
      that.load_player(d);
    });

    play_button.click(function() {
      that.play();
    });

    prev_button.click(function() {
      that.prev();
    });

    next_button.click(function() {
      that.next();
    });
  };

  polyphony.load_player = function(player) {
    if(player==="youtube") this.load_youtube();
    if(player==="soundcloud") this.load_soundcloud();
  }

  polyphony.loaded = function() {
    current_track = 0;
    current_player = playlist[current_track].track_host;
    $("#"+current_player+"-container").removeClass("hide");
  }
  
  polyphony.play = function(track_number, manual) {
    current_track = !isNaN(track_number) ? track_number : current_track;
    
    if(player_state===PLAYING && !track_number) {
      this.pause();
    } else if(player_state===PAUSED && !track_number) {
      $($("#playlist .track-container")[current_track]).removeClass("paused");
      $($("#playlist .track-container")[current_track]).addClass("now-playing");
      if(current_player==="youtube") {
        youtube_player.playVideo();  
      } else if(current_player==="soundcloud") {
        soundcloud_player.play();
      }
      player_state = PLAYING;
    } else {
      if(player_state!=UNDEFINED) {
        this.stop();
      }
      
      $("#playlist .track-container").removeClass("active");
      $("#playlist .track-container").removeClass("now-playing");
      $($("#playlist .track-container")[current_track]).addClass("active");
      $($("#playlist .track-container")[current_track]).addClass("now-playing");
      
      if(current_track>5 && !manual) {
        $("#playlist").scrollTo($("#track"+(current_track-5)))
      } else if(current_track==0) {
        $("#playlist").scrollTo($("#track0"));
      }

      t = playlist[current_track];
      $("#stp-info .title").text(t.title);
      $("#stp-info .source").html(
        '<p><i class="fa fa-comment"></i> Join the discussion at <a href="' + t.mention_url+ '" target="_blank">' + 
          t.mention_title + '</a></p><p>via ' + t.data_source_name + '</p>'
      );
      if(!t) {
        //Error
      }
      if(t.track_host==="youtube") {
        this.play_youtube(t);
        player_state=PLAYING;
      } else if(t.track_host==="soundcloud") {
        this.play_soundcloud(t);
        player_state=PLAYING;
      }
    }

    players.forEach(function(d) {
      if(d===current_player) {
        $("#"+d+"-container").removeClass("hide");
      } else {
        $("#"+d+"-container").addClass("hide");
      }
    });
  };

  polyphony.stop = function() {
    player_state=STOPPED;
    if(current_player==="youtube") {
      youtube_player.stopVideo();
    }
    if(current_player==="soundcloud") {
      soundcloud_player.pause();
    }
  }

  polyphony.pause = function() {
    if(current_player==="youtube") {
      youtube_player.pauseVideo();
      player_state=PAUSED;
    }
    if(current_player==="soundcloud") {
      soundcloud_player.pause();
      player_state=PAUSED;
    }
    $($("#playlist .track-container")[current_track]).removeClass("now-playing");
    $($("#playlist .track-container")[current_track]).addClass("paused");
  }

  polyphony.prev = function(options) {
    current_track = current_track===0 ? playlist.length-1 : current_track-1 ;
    this.stop();
    this.play();
  };

  polyphony.next = function(options) {
    current_track = current_track===playlist.length-1 ? 0 : current_track+1 ;
    this.stop();
    this.play();
  };

  polyphony.refresh_playlist = function() {
    $("#playlist").empty();
    var i =0;
    var that = this;

    playlist.forEach(function(track) {
      $("#playlist").append(
        '<div class="list-group-item track-container" data-track-number="' + i + '" id="track' + i + '">' + 
          '<div class="row track">' +
            '<div class="col-md-10">' +
              //Starring - Work in progress
              //'<div class="track-title"><i class="fa fa-star star-button" data-track-id="' + track.id + '" data-track-host="' + track.track_host + '"></i>' + 
              '<div class="track-title">' + 
                track.title.substring(0,70) + (track.title.length>=70 ? '...' : '') + '</div>' +
            '</div>' + 
            '<div class="col-md-2">' + 
              '<div class="track-length">' + track.duration + '</div>' + 
            '</div>' + 
          '</div>' +
        '</div>'
      );
      i++;
    });

    if(player_state===PLAYING) {
      $("#playlist .track-container").removeClass("active");
      $("#playlist .track-container").removeClass("now-playing");
      $($("#playlist .track-container")[current_track]).addClass("active");
      $($("#playlist .track-container")[current_track]).addClass("now-playing");
    }

    $(".track-container").click(function(e) {
      e.preventDefault();
      var track_number = $(this).data("track-number");
      that.play(track_number,true);
    });

    //Starring - Work in progress
    /*
    $(".star-button").hover(
      function() {
        $(this).addClass("starring");
      },
      function() {
        $(this).removeClass("starring");
      }
    );

    $(".star-button").click(function(event) {
      event.preventDefault();
      event.stopPropagation();
      var track_id = $(this).data("track-id");
      var track_host = $(this).data("track-host");
      var track = playlist.filter(function(d) {
        return d.id===track_id && d.track_host==track_host;
      }).shift();
      if(track) {
        var starred_playlist = JSON.parse(localStorage.getItem("starred_playlist"));
        if(!starred_playlist) {
          starred_playlist = [track];
        } else {
          starred_playlist.push(track);
        }
        localStorage.setItem("starred_playlist", JSON.stringify(starred_playlist));
        $(this).addClass("starred");
      }
    });
    */
  }

  polyphony.update_playlist = function() {
    var that = this;
    var request_url = "/playlist" + (data_sources ? "?data_sources="+data_sources.join(",") : "");
    $.ajax(request_url).done(function(data) {
      playlist = playlist.concat(data.playlist.filter(function(d) {
        return !playlist.some(function(x) {
          return d.id===x.id;
        });
      }));
      that.refresh_playlist();
    });
    setTimeout(function() {
      that.update_playlist();
    }, 1800000);
  }

  polyphony.set_playlist = function(p) {
    playlist = p;
  }

  polyphony.set_data_sources = function(d) {
    data_sources = d;
  }

  /* YouTube */

  polyphony.load_youtube = function(options) {
    var tag = document.createElement('script');
    tag.src = "https://www.youtube.com/iframe_api";
    var firstScriptTag = document.getElementsByTagName('script')[0];
    firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
  };

  polyphony.youtube_ready = function(options) {
    var that = this;
    
    first_youtube_track = $.grep(playlist, function(d) {
      return d.track_host==="youtube";
    })[0];
    if(!first_youtube_track) {
      first_youtube_track = {"id": "EyljKGIJM0Q"}
    }
    youtube_player = new YT.Player('youtube', {
      width:'100%',
      playerVars: {
        modestbranding:1,
        showinfo:0,
        controls:1,
        autohide:1,
        iv_load_policy:3
      },
      videoId: first_youtube_track.id,
      events: {
        'onError': function(event) {
          playlist.splice(current_track--,1);
          that.refresh_playlist();
          setTimeout(function() {
            that.next();
          }, 2000);
        },
        'onStateChange': function(event) {
          if (event.data === YT.PlayerState.PAUSED) {
            play_button.find("i").removeClass("fa-pause");
            play_button.find("i").addClass("fa-play");
            $($("#playlist .track-container")[current_track]).removeClass("now-playing");
            $($("#playlist .track-container")[current_track]).addClass("paused");
            player_state = PAUSED;
          }
          if (event.data === YT.PlayerState.PLAYING) {
            play_button.find("i").removeClass("fa-play");
            play_button.find("i").addClass("fa-pause");
            $($("#playlist .track-container")[current_track]).removeClass("paused");
            $($("#playlist .track-container")[current_track]).addClass("now-playing");
            player_state = PLAYING;
          }
          if (event.data === YT.PlayerState.ENDED) {
            that.next();
          }
        }
      }
    });
    players_loaded.push("youtube");
    if($(players).not(players_loaded).length === 0 && $(players_loaded).not(players).length === 0) {
      this.loaded();
    }
  }

  polyphony.play_youtube = function(track) {
    current_player = "youtube";
    youtube_player.loadVideoById({
      videoId:track.id
    });
  }

  /* SoundCloud */

  polyphony.load_soundcloud = function(options) {
    var that = this;
    SC.initialize({
      client_id: 'd3012111d6ea13fa210b214f82b7be3a'
    });
    first_soundcloud_track = $.grep(playlist, function(d) {
      return d.track_host==="soundcloud";
    })[0];
    if(!first_soundcloud_track) {
      first_soundcloud_track = 193;
    }
    $("#soundcloud").attr("src","https://w.soundcloud.com/player/?url=http://api.soundcloud.com/tracks/"+first_soundcloud_track.id+"&visual=true");
    $("#soundcloud").attr("width","100%");
    $("#soundcloud").attr("height","360");
    soundcloud_player = SC.Widget("soundcloud");

    soundcloud_player.bind(SC.Widget.Events.PLAY, function() {
      play_button.find("i").removeClass("fa-play");
      play_button.find("i").addClass("fa-pause");
      $($("#playlist .track-container")[current_track]).removeClass("paused");
      $($("#playlist .track-container")[current_track]).addClass("now-playing");
      player_state = PLAYING;
    });

    soundcloud_player.bind(SC.Widget.Events.PAUSE, function() {
      play_button.find("i").removeClass("fa-pause");
      play_button.find("i").addClass("fa-play");
      $($("#playlist .track-container")[current_track]).removeClass("now-playing");
      $($("#playlist .track-container")[current_track]).addClass("paused");
      player_state = PAUSED;
    });

    soundcloud_player.bind(SC.Widget.Events.FINISH, function() {
      that.next();
    });

    players_loaded.push("soundcloud");
    if($(players).not(players_loaded).length === 0 && $(players_loaded).not(players).length === 0) {
      this.loaded();
    }
  }

  polyphony.play_soundcloud = function(track) {
    current_player = "soundcloud";
    soundcloud_player.load("http://api.soundcloud.com/tracks/"+track.id+"&visual=true");
    soundcloud_player.bind(SC.Widget.Events.READY, function() {
      soundcloud_player.play();
    });
  }

  this.polyphony = polyphony;

}();