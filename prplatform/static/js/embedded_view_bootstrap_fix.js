
// never ever do something like this. anywhere. for any reason.

// the pages that include this snippet of javascript are embedded
// in a different website (A+) that uses bootstrap 3 instead of
// bootstrap 4 which PRP uses. bs4 uses rem sizing for everything
// whereas bs3 uses pixels. since the root element's font-size
// is set to 10 px in bs3, everything breaks on the embedded
// page --> everything looks too small.
// to "fix" this we change the font-size of the page that
// embeds our pages. this doesn't seem to have any effect on the
// layout of the embedding page but makes our pages work.

document.querySelector('html').style.fontSize = '14px';

