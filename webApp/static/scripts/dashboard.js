
function scroll_to_tweet(id) {
    $(".tweet").removeClass("hover-tweet") // remove existing hover-tweet class
    $("#" + id + "").addClass("hover-tweet") // add hover-class to hover tweet

    var tweet_pos = $("#" + id + "").offset().top
    var first_tweet_pos = $(".tweet").offset().top
    var to_scroll = tweet_pos - first_tweet_pos
    $("#tweets-list").animate({ scrollTop: to_scroll}, "fast");
}

$("body").on('DOMSubtreeModified', "#selected-tweet", function() {
    var tweet_id = $("#selected-tweet").text();
    scroll_to_tweet(tweet_id);
});