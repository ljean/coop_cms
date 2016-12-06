$(function() {
    
    $.fn.rolloverify = function(options) {
        
        var idx = 0;
        var images = [];
        var elt0 = null;
        
        //fill an array with the src of images to display
        $(this).find('img').each(function(index, elt) {
            images.push($(elt).attr('src'));
            if (index==0) {
                elt0 = elt; //1st element: keep it
                $(elt).addClass('coop-rollover');
                $(elt).css("width", "").css("height", "");
            } else {
                $(elt).hide(); //hide others
            }
        });
        
        //if period is not defined, change every 5s
        var period = 5000;
        if (options && options.period) {
            period = options.period;
        }
        
        if (elt0!=null) {
            //The function change the src of the img every N seconds
            var rollover = function() {
                setTimeout(
                    function() {
                        idx++;
                        if (idx >= images.length) {
                            idx = 0;
                        }
                        $(elt0).attr('src', images[idx]);
                        rollover();
                    },
                    period
                )
            };
            rollover();
        }
    };
});
