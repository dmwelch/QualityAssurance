# Logic description for module

def constructFilename():
    outputs = QADatabase.runGenericQuery(self.parser.get("GetUnreviewed", "query"))
    recordID = outputs[0]
    dirs = outputs[1:]
    return dirs, recordID

def onLoadPushButtonClicked():
    recordID, dirs = constructFilename()
    volumeFiles = ['t1_average_BRAINSABC.nii.gz',
                   't2_average_BRAINSABC.nii.gz']
    labelFiles = ['l_caudate_seg.nii.gz', 'l_accumben_seg.nii.gz',
                  'r_caudate_seg.nii.gz', 'r_accumben_seg.nii.gz']
    loadData(dirs, 'TissueClassify', volumeFiles, 'volume')
    loadData(dirs, 'TissueClassify', ['fixed_brainlabels_seg.nii.gz'], 'labelmap')
    loadData(dirs, 'DenoisedRFSegmentations', labelFiles, 'labelmap')

def loadData(dirs, base, files, kind):
    for filename in files:
        filepath = os.path.join(*dirs, base, filename)
        self.loadData(filename, kind=kind)
