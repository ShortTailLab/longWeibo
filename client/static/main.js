function setupFileUpload($root)
{
    var $uploader = $root.find('#fileupload');
    var $image = $root.find('img');
    var $p = $root.find('p');

    $root.find('#fileupload').fileupload(
    {
        url : '/upload',
        sequentialUploads: true,
        dataType : 'json',
        dropZone: $root,
        done: function (e, data) 
        {
            console.log("upload finished");
            
            // play an animation here
            $p.hide();
            $image.attr('src', data.result.thunmnail_url)
                .load( function()
                {
                    console.log($image);
                    console.log($image.width());
                    $root.find('.image-box').css('width', $image.width());
                });
            $image.show();

            $uploader.fileupload('destroy');
            
            console.log($image.width());
            console.log(e);
            console.log(data);
        },

        progress: function(e, data)
        {
            var progress = parseInt(data.loaded / data.total * 100, 10); 
            $p.html(progress + "%");
            console.log("Upload progress: " + progress + "%");
        },

        added: function(e, data)
        {
            console.log("file added to upload");
        },

        fail: function(e, data)
        {
            console.log("file upload failed");
        },
    });
}

function postToRender($stuff)
{
    $.post('/render', { content : $stuff.html() }, function(data)
    {
        if(data.success)
        {
            console.log(data);
        }
    });
}

function createTextItem(defaultText)
{
    // clone
    //var $item = $.extend(true, {}, $("#template-lib #_text-item li"));
    var $item = $("#template-lib #_text-item li").clone();
    if(defaultText)
    {
        $item.find("textarea").val(defaultText);
    }

    $item.find("textarea").TextAreaExpander(50);
    return $item;
}

function createImageItem(image_url)
{
    // clone
    //var $item = $.extend(true, {}, $("#template-lib #_image-item li"));
    var $item = $("#template-lib #_image-item li").clone();
    $item.find("img").attr("src", image_url);

    setupFileUpload($item);

    return $item;
}

$(function () 
{
    $(document).bind('drop dragover', function(e)
    {
        e.preventDefault();
    });

    $('#doc').sortable(
    { 
        opacity: 0.7, 
        placeholder : "box-highlight",
        
        stop: function(event, ui)
        {
            // only detect tool buttons
            if(ui.item.hasClass("tool-button"))
            {
                if(ui.item.hasClass("add-text"))
                {
                    ui.item.replaceWith( createTextItem() );
                }
                else if(ui.item.hasClass("add-image"))
                {
                    ui.item.replaceWith( createImageItem() );
                }
            }
        }
        
    });

    // add text button
    $('#tool-add-text').draggable(
    {
        connectToSortable : "#doc",
        helper : function(event) { return "<div></div>"; }, 
        revert : 'invalid',
    });

    $("#tool-add-text").click(function()
    {
        $item = createTextItem();
        $("#doc").append($item);
    });

    // add image button
    $("#tool-add-image").click(function()
    {
        $item = createImageItem();
        $("#doc").append($item);
    });

    $('#tool-add-image').draggable(
    {
        connectToSortable: '#doc',
        helper : function(event) { return "<div></div>"; },
        revert : 'invalid',
    });
    
    // trash area
    $('#tool-trash').droppable(
    {
        hoverClass : "box-highlight",
        accept: '#doc *',
        drop : function(event, ui)
        {
            $(ui.draggable).remove(); 
        },
        tolerance: 'pointer',
    });

    $('#tool-render').click(function()
    {
        postToRender($('#doc'));
    });

    // example items to insert
    $item1 = createTextItem();
    $item2 = createImageItem("https://www.google.com/images/srpr/logo3w.png");

    $list = $("#doc");
    $list.append($item1);
    $list.append($item2);
    // end of example

});

