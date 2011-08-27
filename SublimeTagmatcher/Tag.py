import sublime, sublime_plugin, Matcher

class TagCommand(sublime_plugin.EventListener):
  def on_selection_modified(self, view):
    selRegion = view.sel()
    if(selRegion[0].a != selRegion[0].b):
      view.add_regions(
        'highlight', 
        [], 
        'entity.name.class',
        'dot',
        sublime.DRAW_OUTLINED
      )
      return 0

    bufferSize = view.size()
    bufferRegion = sublime.Region(0, bufferSize)
    bufferText = view.substr(bufferRegion)
    curPosition = selRegion[0].b
    foundTags = Matcher.match(bufferText, curPosition, 'html')
    tag1 = { "match": foundTags[0] }
    tag2 = { "match": foundTags[1] }
    if( str(tag1['match']) != 'None' and 
        view.substr(tag1['match'] + 1) != '!' and 
        view.substr(tag1['match'] - 1) != '`' and 
        view.substr(tag1['match']) == '<' and 
        view.substr(curPosition) != '<'):

      # Get 1st Tag
      tag1['begin'] = tag1['match']
      tag1['end'] = tag1['match']
      while(view.substr(tag1['end']) != '>'):
        tag1['end'] = tag1['end'] + 1
      tag1['region'] = sublime.Region(tag1['begin'], tag1['end'] + 1)

      # Get 2nd Tag
      tag2['end'] = tag2['match'] - 1
      tag2['begin'] = tag2['end']
      while(view.substr(tag2['begin']) != '<'):
        tag2['begin'] = tag2['begin'] - 1
      tag2['region'] = sublime.Region(tag2['begin'], tag2['end'] + 1)

      # Highlight
      lightRegions = [tag1['region'], tag2['region']]
      view.add_regions(
        'highlight', 
        lightRegions, 
        'entity.name.class',
        'dot',
        sublime.DRAW_OUTLINED
       )

    else:
      view.add_regions(
        'highlight', 
        [], 
        'entity.name.class',
        'dot',
        sublime.DRAW_OUTLINED
      )