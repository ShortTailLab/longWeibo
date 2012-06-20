function setupFileUpload($root)
{
    var $uploader = $root.find('#fileupload');
    var $image = $root.find('.user-image');
    var $p = $root.find('p');

    $root.find('#fileupload').fileupload(
    {
        url : '/upload',
        sequentialUploads: true,
        dataType : 'json',
        dropZone: $root,

        done: function (e, data) 
        {
            if(data.result.success)
            {
                $p.hide(); // hide progress text

                $image.attr('src', data.result.thunmnail_url)
                    .load( function()
                    {
                        var $imagebox = $root.find('.image-box');
                        var w = $image.width() > $imagebox.width() ? $imagebox.width() : $image.width();
                        $imagebox.css('width', w);
                        //$image.css('width', w);
                    });
                $image.fadeIn();

                $uploader.fileupload('destroy');
            }
            else
            {
                alert("文件太大了，最大为2 MB");
            }
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

function textItemJson(text, height, style)
{
    return { type : 'text', text : text, height : height, style : style };
}

function imageItemJson(url, width)
{
    return { type : 'image', image_url : url, width : width };
}

function getClasses($item)
{
    var classStr = "";
    classStr += $item.hasClass("align-1") ? "align-1" : 
                 $item.hasClass("align-2") ? "align-2" : "";
    classStr += " ";
    classStr += $item.hasClass("style-1") ? "style-1" : 
                    $item.hasClass("style-2") ? "style-2" :
                    $item.hasClass("style-3") ? "style-3" : "";
    return classStr;
}

/*****
  generate a list of json objects for rendering
 *****/
function postToRender($stuff)
{
    //$('#tool-render-result').hide();
    $('#tool-render-result').html("正在生成图片");

    var itemList = [];
    $stuff.children().each( function()
    {
        if( $(this).find('.text-box').length > 0 )
        {
            var $textarea = $(this).find('textarea');
            var text = $textarea.val();
            var hint = $textarea.attr('title');
            var height = $textarea.height();

            if(text != '' && text != hint)
            {
                var style = getClasses($textarea);
                itemList.push( textItemJson(text, height, style) );
            }
        }
        else if( $(this).find('.image-box').length > 0 )
        {
            var image_url = $(this).find('.user-image').attr('src');
            var width = $(this).find('.user-image').width();
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
            $('#tool-render-result').html('<a target="_blank" href="' + data.image_url + '">做好了.</a>');
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


function transparent(elem)
{
    $(elem).css('opacity','0');
}

function opaque(elem)
{
    $(elem).css('opacity','0.5');
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
        axis : 'y',
        
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
    /*
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
     */

    $('#tool-render').click(function()
    {
        postToRender($('#doc'));
    });

    // text area auto hint
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

    // hover show / hide buttons
    $('html').on('mouseover', '.text-box, .image-box', function()
    {
        opaque( $(this).find('.remove-button, .style-button, .position-button') );
    });

    $('html').on('mouseout', '.text-box, .image-box', function()
    {
        transparent( $(this).find('.remove-button, .style-button, .position-button') );
    });

    // remove button event
    $('html').on('click', '.image-box .remove-button, .text-box .remove-button', function()
    {
        var $button = $(this);
        //promptDelete( function(){ $button.parents("li").remove() } );
        $button.parents("li").remove();
    });

    // style button
    $('html').on('click', '.text-box .style-button', function()
    {
        var $button = $(this);
        //promptDelete( function(){ $button.parents("li").remove() } );
        var $text = $button.siblings("textarea");
        if( $text.hasClass("style-1") )
        {
            $text.removeClass("style-1");
            $text.addClass("style-2");
        }
        else if( $text.hasClass("style-2") )
        {
            $text.removeClass("style-2");
            $text.addClass("style-3");
        }
        else if( $text.hasClass("style-3") )
        {
            $text.removeClass("style-3");
            $text.addClass("style-1");
        }
    });

    // align button
    $('html').on('click', '.text-box .position-button', function()
    {
        var $button = $(this);
        var $text = $button.siblings("textarea");

        if( $text.hasClass("align-1") )
        {
            $text.removeClass("align-1");
            $text.addClass("align-2");
        }
        else if( $text.hasClass("align-2") )
        {
            $text.removeClass("align-2");
            $text.addClass("align-1");
        }
    })

    // example items to insert
    $list = $("#doc");
    $list.append( createTextItem() );
    $list.append( createImageItem() );
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

function promptDelete(f)
{
    $.prompt('确认删除?',
    {
		overlayspeed:'fast',
		buttons: { 确定:true, 取消:false },
        callback: function(event, value)
        {
            if(value)
            {
                f();
            }
        }
	});
}

/*
	var $jqi=$.prompt('删除此段?',{
				overlayspeed:'fast',
				buttons: { Ok: true, Cancel: false },
				focus:1,
				})
			
	$jqi.bind('promptsubmit',function(e,v){
			if (window.console)
				if (v=='1'){
					return true
				}
				else
					return false
	});
*/	

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
