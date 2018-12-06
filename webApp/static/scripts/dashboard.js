
function scroll_to_tweet(id) {
    $(".tweet").removeClass("hover-tweet") // remove existing hover-tweet class
    $("#" + id + "").addClass("hover-tweet") // add hover-class to hover tweet

    var tweet_pos = $("#" + id + "").offset().top // position of hover tweet
    var first_tweet_pos = $(".tweet").offset().top // position of first tweet
    var to_scroll = tweet_pos - first_tweet_pos
    $("#tweets-list").animate({ scrollTop: to_scroll}, "fast"); // scroll
}

$("body").on('DOMSubtreeModified', "#selected-tweet", function() { // when there is a new tweet selected
    var tweet_id = $("#selected-tweet").text();
    scroll_to_tweet(tweet_id); // launch the function for the id in the div
});