function setupFileUpload($root)
{
    var $uploader = $root.find('#fileupload');
    var $image = $root.find('.usrIMG');
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
                    var $imagebox = $root.find('.image-box');
                    var w = $image.width() > $imagebox.width() ?$imagebox.width() : $image.width();
                    //$imagebox.css('width', w);
                    $image.css('width', w);
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

function textItemJson(text, height)
{
    return { type : 'text', text : text, height : height };
}

function imageItemJson(url, width)
{
    return { type : 'image', image_url : url, width : width };
}

function postToRender($stuff)
{
    $('#tool-render-result').hide();

    var itemList = [];
    $stuff.children().each( function()
    {
        if( $(this).hasClass('text-box') )
        {
            var text = $(this).find('textarea').val();
            var hint = $(this).find('textarea').attr('title');
            var height = $(this).find('textarea').height();

            if(text != '' && text != hint)
            {
                itemList.push( textItemJson(text, height) );
            }
        }
        else if( $(this).find('.image-box') )
        {
            var image_url = $(this).find('img').attr('src');
            var width = $(this).find('img').width();
            if( image_url != '' )
            {
                itemList.push( imageItemJson(image_url, width) );
            }
        }
    });
    console.log( itemList );

    $.post('/render', { itemList : JSON.stringify(itemList) }, function(data)
    {
        if(data.success)
        {
            $('#tool-render-result').html('<a target="_blank" href="' + data.image_url + '">URL</a>');
            $('#tool-render-result').slideDown();
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
    else
    {
        $item.find("textarea").val( $item.find('textarea').attr('title'));
    }

    $item.find("textarea").TextAreaExpander(50);
    return $item;
}

function createImageItem(image_url)
{
    // clone
    //var $item = $.extend(true, {}, $("#template-lib #_image-item li"));
    var $item = $("#template-lib #_image-item li").clone();
    $item.find(".usrIMG #usrIMG").attr("src", image_url);

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
        helper : 'clone',
        
        /*function(event)
        {
            console.log(event);
            return '<div></div>';
        },*/
        
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
        helper : function(event) { return "<div style='display: none;'></div>"; },
        appendTo: 'body',
        scroll: false,
        revert : 'invalid',
    })
    .click(function()
    {
        $item = createTextItem();
        $("#doc").append($item);
    });

    // add image button
     $('#tool-add-image').draggable(
    {
        connectToSortable: '#doc',
        helper : function(event) { return "<div style='display: none;'></div>"; },
        revert : 'invalid',
        appendTo : 'body',
        scroll : false,
        revert : 'invalid',
    })
    .click(function()
    {
        $item = createImageItem();
        $("#doc").append($item);
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


    $('html').on('focus', 'textarea.autohint', function()
    {
        if( $(this).val() == $(this).attr('title') )
        {
            $(this).val( '' );
            $(this).removeClass('autohint');
        }
    });
    $('html').on('blur', 'textarea.autohint', function()
    {
        if( $(this).val() == '')
        {
            $(this).val( $(this).attr('title') );
            $(this).addClass('autohint');
        }
    });

    // example items to insert
    $item1 = createTextItem();
    $item2 = createImageItem();

    $list = $("#doc");
    $list.append($item1);
    $list.append($item2);
    // end of example

});

function transparent(elem)
{
    $(elem).css('opacity','0');
}

function opaque(elem)
{
    $(elem).css('opacity','0.5');
}
function removeTag(tag,src)
{
    console.log("preparing to remove")
    console.log(tag)
    console.log(src)
    $(tag).remove()
    $.get("/deleteImage?imagePath="+src)
}

/*
function userImgMouse(elem,evtype)
{
    if (evtype="over"){
        $(elem).next().css('opacity', '0.8');
    }
    else{
        $(elem).next().css('opacity','0');
    }


}

*/
