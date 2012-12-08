from win32com.client import constants as const

xsi = Application


def clear_OnClicked():
    prop = get_clip_prop()
    if prop:
        prop.Parameters('names').Value = ''
        prop.Parameters('starts').Value = ''
        prop.Parameters('ends').Value = ''
    refresh()


def fromplaycontrol_OnClicked():
    pc = xsi.Dictionary.GetObject('PlayControl')
    ppg = PPG.Inspected(0)
    ppg.Parameters('clipstart').Value = int(pc.Parameters('In').Value)
    ppg.Parameters('clipend').Value = int(pc.Parameters('Out').Value)


def edit_OnClicked():
    #clip_prop = get_clip_prop()
    ppg = PPG.Inspected(0)
    sel = ppg.Parameters('clips').Value
    if not sel:
        return
    print sel
    name, start, end = sel.split('::')

    ppg.Parameters('clipname').Value = name
    ppg.Parameters('clipstart').Value = start
    ppg.Parameters('clipend').Value = end
    ppg.Parameters('current').Value = sel

    ppg.Parameters('clipname').ReadOnly = False
    ppg.Parameters('clipstart').ReadOnly = False
    ppg.Parameters('clipend').ReadOnly = False
    ppg.Parameters('current').ReadOnly = False
    ppg.PPGLayout.Item('save').SetAttribute('buttondisable', False)
    ppg.PPGLayout.Item('fromplaycontrol').SetAttribute('buttondisable', False)

    PPG.Refresh()


def save_OnClicked():
    clip_prop = get_clip_prop()

    ppg = PPG.Inspected(0)
    name, start, end = ppg.Parameters('current').Value.split('::')

    newname = str(ppg.Parameters('clipname').Value)
    newstart = str(ppg.Parameters('clipstart').Value)
    newend = str(ppg.Parameters('clipend').Value)

    names = clip_prop.Parameters('names').Value
    starts = clip_prop.Parameters('starts').Value
    ends = clip_prop.Parameters('ends').Value

    if not names:
        newnames = (newname,)
        newstarts = (newstart,)
        newends = (newend,)
    else:
        names = names.split('::')
        starts = starts.split('::')
        ends = ends.split('::')
        newnames = []
        newstarts = []
        newends = []
        for index, oldname in enumerate(names):
            if oldname == name:
                newnames.append(newname)
                newstarts.append(newstart)
                newends.append(newend)
                name = 'xxx'
            else:
                newnames.append(oldname)
                newstarts.append(starts[index])
                newends.append(ends[index])

    clip_prop.Parameters('names').Value = '::'.join(newnames)
    clip_prop.Parameters('starts').Value = '::'.join(newstarts)
    clip_prop.Parameters('ends').Value = '::'.join(newends)

    ppg.Parameters('clipname').ReadOnly = True
    ppg.Parameters('clipstart').ReadOnly = True
    ppg.Parameters('clipend').ReadOnly = True
    ppg.Parameters('current').ReadOnly = True
    ppg.PPGLayout.Item('save').SetAttribute('buttondisable', True)
    ppg.PPGLayout.Item('fromplaycontrol').SetAttribute('buttondisable', True)

    refresh()


def add_OnClicked():
    clip_prop = get_clip_prop()

    names = clip_prop.Parameters('names').Value
    starts = clip_prop.Parameters('starts').Value
    ends = clip_prop.Parameters('ends').Value

    if not names:
        names = ('NewClip',)
        starts = ('0',)
        ends = ('100',)
    else:
        names = names.split('::')
        starts = starts.split('::')
        ends = ends.split('::')
        names.append('NewClip')
        starts.append('0')
        ends.append('100')

    clip_prop.Parameters('names').Value = '::'.join(names)
    clip_prop.Parameters('starts').Value = '::'.join(starts)
    clip_prop.Parameters('ends').Value = '::'.join(ends)

    refresh()


def remove_OnClicked():
    clip_prop = get_clip_prop()
    ppg = PPG.Inspected(0)
    sel = ppg.Parameters('clips').Value
    if not sel:
        return
    print sel
    name, start, end = sel.split('::')

    names = clip_prop.Parameters('names').Value
    starts = clip_prop.Parameters('starts').Value
    ends = clip_prop.Parameters('ends').Value

    if not names:
        names = []
        starts = []
        ends = []
    else:
        names = names.split('::')
        starts = starts.split('::')
        ends = ends.split('::')
        names.remove(name)
        starts.remove(start)
        ends.remove(end)

    clip_prop.Parameters('names').Value = '::'.join(names)
    clip_prop.Parameters('starts').Value = '::'.join(starts)
    clip_prop.Parameters('ends').Value = '::'.join(ends)

    refresh()


def refresh():
    clip_prop = get_clip_prop()
    if not clip_prop:
        print 'no prop'
        return
    clips = get_ui_clips(clip_prop)
    PPG.Inspected(0).PPGLayout.Item('clips').UIItems = clips
    PPG.Refresh()


def get_clip_prop():
    clip_prop = None
    for prop in xsi.ActiveSceneRoot.Properties:
        if prop.Name == 'SoftCryAnimationClips':
            clip_prop = prop
    return clip_prop


def get_ui_clips(prop):
    names = prop.Parameters('names').Value
    starts = prop.Parameters('starts').Value
    ends = prop.Parameters('ends').Value
    if (not names) or (not starts) or (not ends):
        return ()
    names = names.split('::')
    starts = starts.split('::')
    ends = ends.split('::')
    clips = []
    for n in xrange(len(names)):
        clips.append('{0}: {1} - {2}'.format(names[n], starts[n], ends[n]))
        clips.append('{0}::{1}::{2}'.format(names[n], starts[n], ends[n]))
    return clips


def get_clips(prop):
    names = prop.Parameters('names').Value.split('::')
    starts = prop.Parameters('starts').Value.split('::')
    ends = prop.Parameters('ends').Value.split('::')
    clips = []
    for n in xrange(len(names)):
        clips.append((names[n], int(starts[n]), int(ends[n])))
    return clips
