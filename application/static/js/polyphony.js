!function(){
  var polyphony={
    version:"0.1"
  };

  var PLAYING=1, PAUSED=2, STOPPED=-1, UNDEFINED=-2;
  var players= ["youtube", "soundcloud"];
  var players_loaded = [],
      playlist = [],
      data_sources = [],
      current_track = 0,
      youtube_player = null,
      soundcloud_player = null,
      current_player = null,
      player_state = UNDEFINED,
      default_playlist = null,
      current_playlist = null;

  var play_button, prev_button, next_button;

  polyphony.initialize = function(options) {
    playlist = default_playlist = current_playlist = options.playlist || [];

    play_button = $("#" + (options.play_button || "ppp-play"));
    prev_button = $("#" + (options.prev_button || "ppp-prev"));
    next_button = $("#" + (options.prev_button || "ppp-next"));

    var that = this;

    // Load all players
    players.forEach(function(d) {
      that.load_player(d);
    });

    //Set up buttons
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
  };

  polyphony.set_player = function(player) {
    current_player = player;
    players.forEach(function(d) {
      $("#"+d+"-container").addClass("hide");
    });
    $("#"+player+"-container").removeClass("hide");
  };

  polyphony.players_loaded = function() {
    // All players are now loaded
    
    // Hide all other players except for the first track
    first_track = current_playlist[0];
    current_player = first_track.track_host;
    this.set_player(current_player);

    // Refresh playlist
    console.log("refreshing...")
    this.refresh_playlist();
  };

  polyphony.show_info = function(track) {
    $("#ppp-info .title").text(track.title);
    $("#ppp-info .source").html(
      '<a href="' + track.mention_url+ '" target="_blank"><i class="fa fa-comment"></i> ' + 
        track.data_source_name + ' : ' + (track.mention_title.substring(0,50) + (track.mention_title.length>=50 ? '...' : '')) + '</a>'
    );
  };
  
  polyphony.play = function(track_number, manual) {
    // If track_number isNaN, that means the function is being triggered
    // by button clicks. If manual is true, it was triggered by user clicking
    // on a track in the playlist which lets us know not to scroll to the middle.

    current_track = !isNaN(track_number) ? track_number : current_track;
    
    if(player_state===PLAYING && isNaN(track_number)) {

      // Play button was clicked while playing
      this.pause();

    } else if(player_state===PAUSED && isNaN(track_number)) {
      
      // Play button was clicked while paused
      
      // Change button state
      $($("#playlist .track-container")[current_track]).removeClass("paused");
      $($("#playlist .track-container")[current_track]).addClass("now-playing");

      // Play the track
      if(current_player==="youtube") {
        youtube_player.playVideo();  
      } else if(current_player==="soundcloud") {
        soundcloud_player.play();
      }

      player_state = PLAYING;

    } else {

      // Play button was clicked for the first time
      // or after a new playlist was chosen.

      // ?
      if(player_state!=UNDEFINED) {
        this.stop();
      }


      // Change state of item in playlist
      $("#playlist .track-container").removeClass("active");
      $("#playlist .track-container").removeClass("now-playing");
      $($("#playlist .track-container")[current_track]).addClass("active");
      $($("#playlist .track-container")[current_track]).addClass("now-playing");
      
      
      // Auto-scroll to middle, unless manual selection
      if(current_track>5 && !manual) {
        $("#playlist").scrollTo($("#track"+(current_track-5)))
      } else if(current_track==0) {
        $("#playlist").scrollTo($("#track0"));
      }


      // Get the current track and show info
      t = current_playlist[current_track];
      this.show_info(t);
      
      if(!t) {
        //Error
      }

      // Play the selected track
      if(t.track_host==="youtube") {
        this.play_youtube(t);
        player_state=PLAYING;
      } else if(t.track_host==="soundcloud") {
        this.play_soundcloud(t);
        player_state=PLAYING;
      }

    }

    // Hide all other players except for current track's player
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
    play_button.find("i").removeClass("fa-pause");
    play_button.find("i").addClass("fa-play");
  };

  polyphony.pause = function() {
    if(current_player==="youtube") {
      youtube_player.pauseVideo();
      player_state=PAUSED;
    }
    if(current_player==="soundcloud") {
      soundcloud_player.pause();
      player_state=PAUSED;
    }

    // Change state of item in playlist
    $($("#playlist .track-container")[current_track]).removeClass("now-playing");
    $($("#playlist .track-container")[current_track]).addClass("paused");
  };

  polyphony.prev = function(options) {
    current_track = current_track===0 ? current_playlist.length-1 : current_track-1 ;
    this.stop();
    this.play();
  };

  polyphony.next = function(options) {
    current_track = current_track===current_playlist.length-1 ? 0 : current_track+1 ;
    this.stop();
    this.play();
  };

  polyphony.show_saved_playlists = function() {
    var that = this;

    // Load starred playlist from local storage
    var starred_playlist = JSON.parse(localStorage.getItem("starred_playlist"));
    
    // Add or remove starred playlist menu item to sidebar
    if(starred_playlist) {
      if(!$('[data-name="starred_playlist"]').length) {
        $("#saved-playlists-list").append('<li class="list-group-item"><a class="saved-playlist" data-name="starred_playlist" href="#"><i class="fa fa-star"></i> Starred Songs</a></li>');
      }
    } else {
      $("#saved-playlists-list").find('[data-name="starred_playlist"]').remove();
    }

    // Load custom playlists from local storage
    var saved_playlists = JSON.parse(localStorage.getItem("saved_playlists")) || [];

    // Add custom playlists menu items to sidebar
    saved_playlists.forEach(function(d) {
      var exists = $("#saved-playlists-list").find('[data-name="'+d.name+'"]').length;
      console.log(exists);
      if (!exists) {
        $("#saved-playlists-list").append('<li class="list-group-item"><a class="saved-playlist" data-name="' + d.name + '" href="#"><i class="fa fa-music"></i> ' + d.name + '</a></li>');
        $("#playlist-dropdown").append(
          '<a href="#" class="add-to-playlist list-group-item" data-playlist-name="' + d.name + '" data-track-number="">' +
            '<span><i class="fa fa-music"></i></span>' +
            '<span>'+ d.name + '</span>' +
          '</a>'
        );
        $('.add-to-playlist').click(function(event) {
          event.preventDefault();
          event.stopPropagation();
          var t = $(this).data("track-number");
          if($(this).data("playlist-name")==="new-playlist") {
            console.log(t);
            $("#new-playlist-track").val(t);
            $("#new-playlist-modal").modal("show");
            console.log($("#new-playlist-track").val());
          } else {
            console.log(t);
            var track_to_add = current_playlist[t];
            console.log(track_to_add);
            that.add_to_playlist($(this).data("playlist-name"), track_to_add);
          }
        });
      }
    });

    // Set up sidebar menu item click handler
    $(".saved-playlist").click(function(event) {
      event.preventDefault();
      $("#saved-playlists-list").find("li").removeClass("active");
      $(this).parent().addClass("active");
      
      that.load_playlist($(this).data("name"));
    });
  };

  polyphony.create_playlist = function(playlist_name, track) {
    var saved_playlists = JSON.parse(localStorage.getItem("saved_playlists")) || [];

    if($.grep(saved_playlists, function(d) {
      return d.name.toLowerCase()===playlist_name.toLowerCase();
    }).length) {
      // Playlist with given name already exists, return false
      console.log("already exists");
      return false;
    }
    new_playlist = {
      "name": playlist_name,
      "tracks": [track]
    };
    saved_playlists.push(new_playlist);
    localStorage.setItem("saved_playlists", JSON.stringify(saved_playlists));
    return true;
  };

  polyphony.add_to_playlist = function(playlist_name, track) {
    var saved_playlists = JSON.parse(localStorage.getItem("saved_playlists")) || [];

    playlist_to_add = saved_playlists.filter(function(d) {
      return d.name.toLowerCase()===playlist_name.toLowerCase();
    }).shift();
    var exists = $.grep(playlist_to_add.tracks, function(d) {
      return d.id===track.id;
    }).length;

    if (exists) {
      console.log("Track already in playlist");
    } else {
      console.log("Adding " + track.title + " to " + playlist_to_add.name);
      playlist_to_add.tracks.push(track);
      localStorage.setItem("saved_playlists", JSON.stringify(saved_playlists));
    }
    $("#playlist-dropdown").find('[data-playlist-name="' + playlist_name + '"]').addClass("active");
    $("#playlist-dropdown").fadeOut("slow", function() {
      $("#playlist-dropdown").find('[data-playlist-name="' + playlist_name + '"]').removeClass("active");
    });
  };

  // Given a playlist name, load it and set up to play
  polyphony.load_playlist = function(playlist_name) {
    
    // If currently playing, stop it
    if(player_state===PLAYING) {
      this.stop();
    }

    // If selected playlist is the starred playlist, load it from local storage
    if(playlist_name==="starred_playlist") {

      var starred_playlist = JSON.parse(localStorage.getItem("starred_playlist"));

      // Set current playlist to starred playlist
      if(starred_playlist) {
        this.set_playlist(starred_playlist);

        $("#current-playlist-name").text("Starred Songs");
      }

    }

    // If selected playlist is the default, switch to it
    if(playlist_name==="default_playlist") {
      this.set_playlist(default_playlist);
      $("#current-playlist-name").text("Hot Around the Web");
    }

    // If selected playlist is a custom playlist, load it from local storage
    var saved_playlists = JSON.parse(localStorage.getItem("saved_playlists")) || [];
    var playlist_to_load = saved_playlists.filter(function(d) {
      return d.name===playlist_name;
    }).shift();

    if(!playlist_to_load) return;

    this.set_playlist(playlist_to_load.tracks);
    $("#current-playlist-name").text(playlist_to_load.name);
    $("#playlist").scrollTo($("#track0"));
  };

  polyphony.refresh_playlist = function() {
    // If playing a track, stop it first
    if(player_state===PLAYING) {
      this.stop();
    }
    
    // Empty the playlist div
    $("#playlist").empty();
    
    var i =0;
    var that = this;
    current_track = 0;

    // Load starred tracks from local storage
    var starred_playlist = JSON.parse(localStorage.getItem("starred_playlist"));


    current_playlist.forEach(function(track) {

      // If track is starred, mark it as such
      if(starred_playlist) {
        var starred = $.grep(starred_playlist,function(d) {
          return d.id==track.id && d.track_host==track.track_host;
        }).length ? "starred" : "";
      } else {
        starred = "";
      }
      
      // Construct playlist div
      $("#playlist").append(
        '<div class="list-group-item track-container" data-track-number="' + i + '" id="track' + i + '">' + 
          '<div class="row track">' +
            '<div class="col-md-10 col-sm-10 col-xs-10">' +
              '<div class="track-title">' + 
                '<div class="pull-left">' + 
                  '<i class="fa fa-star star-button ' + starred + '" data-track-id="' + track.id + '" data-track-host="' + track.track_host + '"></i>' + 
                  track.title.substring(0,50) + (track.title.length>=50 ? '...' : '') + 
                '</div>' + 
                '<div class="pull-right options hide">' +
                  '<a href="#" class="options-button">' + 
                    '<i class="fa fa-plus"></i>' +
                  '</a>' + 
                '</div>' + 
              '</div>' +
            '</div>' + 
            '<div class="col-md-2 col-sm-2 col-xs-2">' + 
              '<div class="track-length">' + track.duration + '</div>' + 
            '</div>' + 
          '</div>' +
        '</div>'
      );

      i++;

      // Setup options button hover
      $(".track-container").hover(
        function() {
          $(this).find(".options").removeClass("hide");
        },
        function() {
          $(this).find(".options").addClass("hide");
        }
      );

    });
    
    /*
    // Setup options dropdown
    var playlist_dropdowns = 
      '<ul class="dropdown-menu">' + 
      '<li><a class="add-to-playlist" data-name="new-playlist" tabindex="-1" href="#"><i class="fa fa-plus"></i> New Playlist</a></li>' + 
      //playlist_list +
      '</ul>';

    $(".options").append(playlist_dropdowns);

    $(".dropdown-toggle").dropdown('toggle');
    */

    $(".options-button").click(function(event) {
      event.preventDefault();
      event.stopPropagation();
      $(this).parent().addClass("override_hide");
      $(this).closest(".track-container").addClass("hovered");
      var t = $(this).closest(".track-container").data("track-number");
      console.log("clicked...");
      $("#playlist-dropdown").removeClass("hide");
      $("#playlist-dropdown").find(".add-to-playlist").data("track-number",t);
      $("#playlist-dropdown").css({
        top: event.pageY,
        left: event.pageX
      }).show();
    });

    $('.add-to-playlist').click(function(event) {
      event.preventDefault();
      event.stopPropagation();
      var t = $(this).data("track-number");
      if($(this).data("playlist-name")==="new-playlist") {
        console.log(t);
        $("#new-playlist-track").val(t);
        $("#new-playlist-modal").modal("show");
        console.log($("#new-playlist-track").val());
      } else {
        console.log(t);
        var track_to_add = current_playlist[t];
        console.log(track_to_add);
        that.add_to_playlist($(this).data("playlist-name"), track_to_add);
      }
    });


    $('body').on('click', function (event) {
      $(".override_hide").removeClass("override_hide");
      $(".list-group-item").removeClass("hovered");
      $("#playlist-dropdown").hide();
    });

    $("#playlist").scroll(function () {
      $(".override_hide").removeClass("override_hide");
      $(".list-group-item").removeClass("hovered");
      $("#playlist-dropdown").hide();
    });

    $("#playlist").click(function () {
      $(".override_hide").removeClass("override_hide");
      $(".list-group-item").removeClass("hovered");
      $("#playlist-dropdown").hide();
    });

    // Reset state of items in playlist
    if(player_state===PLAYING) {
      $("#playlist .track-container").removeClass("active");
      $("#playlist .track-container").removeClass("now-playing");

      $("#playlist .track-container").first().addClass("active");
    }

    // Setup manual track selection
    $(".track-container").click(function(e) {
      console.log("clicked...");
      e.preventDefault();
      var track_number = $(this).data("track-number");
      console.log(track_number);
      that.play(track_number,true);
    });

    // Setup star button hover
    $(".star-button").hover(
      function() {
        $(this).addClass("starring");
      },
      function() {
        $(this).removeClass("starring");
      }
    );

    // Setup star button click
    $(".star-button").click(function(event) {

      // Stop event bubbling so track doesn't play
      event.preventDefault();
      event.stopPropagation();

      // Get track star button was clicked on
      var track_id = $(this).data("track-id");
      var track_host = $(this).data("track-host");
      var track = current_playlist.filter(function(d) {
        return d.id==track_id && d.track_host==track_host;
      }).shift();

      if(track) {
        // Add track to starred playlist
        var starred_playlist = JSON.parse(localStorage.getItem("starred_playlist"));

        if(!starred_playlist) {

          // Starred playlist is empty and this is the first track being starred
          starred_playlist = [track];
          $(this).addClass("starred");

        } else {

          // If track is already starred, unstar it
          var is_starred = $.grep(starred_playlist, function(d) {
            return d.id==track.id && d.track_host==track.track_host;
          }).length;

          if(is_starred) {
            // Remove unstarred track from starred playlist
            starred_playlist = starred_playlist.filter(function(d) {
              return !(d.id==track_id && d.track_host==track_host);
            });

            $(this).removeClass("starred");

            // If starred playlist is now empty, remove from local storage
            if(!starred_playlist.length) {
              localStorage.removeItem("starred_playlist");
            }

          } else {

            // Add track to starred playlist
            starred_playlist.push(track);
            $(this).addClass("starred");

          }

        }

        // Save starred playlist back to local storage, unless it is empty
        if(starred_playlist && starred_playlist.length) {
          localStorage.setItem("starred_playlist", JSON.stringify(starred_playlist));
        }
      }

      // Refresh saved playlists on the sidebar
      that.show_saved_playlists();

    });

    // Set first track active
    $(".track-container").first().addClass("active");

    first_track = current_playlist[0];
    current_player = first_track.track_host;
    if(current_player==="youtube" && youtube_player) {
      this.set_youtube_track(first_track);
    } else if(current_player==="soundcloud" && soundcloud_player) {
      this.set_soundcloud_track(first_track);
    }

    this.set_player(current_player);

    this.show_info(first_track);
  };

  polyphony.update_playlist = function() {
    var that = this;
    var request_url = "/playlist" + (data_sources ? "?data_sources="+data_sources.join(",") : "");
    $.ajax(request_url).done(function(data) {
      default_playlist = default_playlist.concat(data.playlist.filter(function(d) {
        return !default_playlist.some(function(x) {
          return d.id===x.id;
        });
      }));
      current_playlist = default_playlist;
      that.refresh_playlist();
    });
    setTimeout(function() {
      that.update_playlist();
    }, 1800000);
  };

  polyphony.set_playlist = function(p) {
    current_playlist = p;
    this.refresh_playlist();
  };

  polyphony.set_data_sources = function(d) {
    data_sources = d;
    current_playlist = default_playlist = [];
    this.update_playlist();
  };

  polyphony.ready = function() {
    var that = this;
    $('[data-toggle="tooltip"]').tooltip();

    // Set up data source icons
    data_sources = JSON.parse(localStorage.getItem("data_sources"));
    if(data_sources) {
      //$(".data-source").addClass("off");
      data_sources.forEach(function(d) {
        $("#"+d).addClass("on");
      });
    }

    $(".data-source").click(function(event) {
      var source_id = $(this).attr("id");
      event.preventDefault();
      event.stopPropagation();
      $(this).toggleClass("on");

      var data_sources = JSON.parse(localStorage.getItem("data_sources")) || [];
      console.log(data_sources);

      if($.grep(data_sources, function(d) {
        return d===source_id;
      }).length) {
        console.log("removing..."+source_id);
        data_sources = data_sources.filter(function(d) {
          return d!=source_id;
        });
      } else {
        data_sources.push(source_id);
      }
      localStorage.setItem("data_sources",JSON.stringify(data_sources));
      polyphony.set_data_sources(data_sources);
    });

    // Load playlist from server
    $.ajax("/playlist" + (data_sources ? "?data_sources="+data_sources.join(",") : "")).done(function(data) {
      that.initialize({
        playlist:data.playlist,
        data_sources:data_sources
      });
    });
    
    setTimeout(function() {
      that.update_playlist();
    }, 1800000);
    
    this.show_saved_playlists();

    $("button[type='submit']").prop("disabled", false);

    $("#new-playlist-form").submit(function(event) {
      event.preventDefault();
      var track_to_add = current_playlist[$("#new-playlist-track").val()];
      var new_playlist_name = $("#new-playlist-name").val();
      var c = that.create_playlist(new_playlist_name, track_to_add);
      if(c) {
        $('#new-playlist-modal').modal('hide');
        that.show_saved_playlists();
      } else {
        $("#new-playlist-error").text("A playlist with that name already exists. Please enter another name.");
        $("#new-playlist-error").removeClass("hide");
      }
    });
  };

  /* YouTube */

  polyphony.load_youtube = function(options) {
    var tag = document.createElement('script');
    tag.src = "https://www.youtube.com/iframe_api";
    var firstScriptTag = document.getElementsByTagName('script')[0];
    firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
  };

  polyphony.youtube_ready = function(options) {
    var that = this;
    
    first_youtube_track = $.grep(current_playlist, function(d) {
      return d.track_host==="youtube";
    })[0];
    if(!first_youtube_track) {
      first_youtube_track = {"id": "EyljKGIJM0Q"}
    }
    youtube_player = new YT.Player('youtube', {
      width:'100%',
      height:'260',
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
          current_playlist.splice(current_track--,1);
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
      this.players_loaded();
    }
  };

  polyphony.play_youtube = function(track) {
    current_player = "youtube";
    youtube_player.loadVideoById({
      videoId:track.id
    });
  };

  polyphony.set_youtube_track = function(track) {
    console.log(youtube_player, track);
    if(typeof youtube_player.cueVideoById === "function") {
      youtube_player.cueVideoById({
        videoId:track.id
      });
    }
  };

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
    $("#soundcloud").attr("height","260");
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
      this.players_loaded();
    }
  };

  polyphony.play_soundcloud = function(track) {
    current_player = "soundcloud";
    soundcloud_player.load("http://api.soundcloud.com/tracks/"+track.id+"&visual=true");
    soundcloud_player.bind(SC.Widget.Events.READY, function() {
      soundcloud_player.play();
    });
  };

  polyphony.set_soundcloud_track = function(track) {
    console.log(soundcloud_player, track);
    soundcloud_player.load("http://api.soundcloud.com/tracks/"+track.id+"&visual=true");
  };

  this.polyphony = polyphony;

}();

function onYouTubeIframeAPIReady() {
  polyphony.youtube_ready();
}

$(function () {
  polyphony.ready();
});