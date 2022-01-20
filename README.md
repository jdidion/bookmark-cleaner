# Bookmark cleaner

This is a workflow to migrate from Chrome bookmarks to Raindrop (or another service that supports tagging bookmarks).

Bookmarks can be cleaned and/or tagged. Cleaning means removing invalid URLs, i.e. those that don't respond to a `HEAD` request (redirects are followed and SSL errors are ignored by default). Tagging means adding each element of the path in the nested bookmark hierarchy as a tag on the bookmark.

## Steps

1. Run [bookmark cleaner](bookmarks.py) to clean and tag the bookmarks in the Chrome bookmarks JSON file. The default path to the bookmarks file on MacOS is used by default; specify a different argument to `--infile` for other platforms/locations. By default, URLs are checked to ensure they resolve (i.e. respond to a `HEAD` request), but this behavior can be disabled with the `--no-check-urls` option. Invalid bookmarks can be written to a file (using `--invalid-file` option) and/or opened in the default web browser (using `--browse-invalid` option).
    
    ```bash
    python bookmarks.py clean -o Bookmarks.cleaned.json
    ```

2. Use [bookmark converter](bookmarks_json_to_html.html) to convert the cleaned and tagged JSON file to HTML format. The resulting HTML file should be importable by any browser or bookmark management service.
