from __main__ import qt, ctk, vtk, slicer

from MRIChangeDetectorStep import *

class SelectVolumesStep(MRIChangeDetectorStep):

  def __init__(self, stepid):
    self.initialize(stepid)
    self.setName( '1. Select input volumes' )
    self.setDescription( 'Select the baseline and follow-up volumes to be compared.' )
    
    self.__parent = super(SelectVolumesStep, self)

    
  def createUserInterface(self):
    '''
    The interface allows choosing two volumes.
    '''
    self.__layout = self.__parent.createUserInterface()
   
    baselineScanLabel = qt.QLabel( 'Baseline volume:' )
    self.__baselineVolumeSelector = slicer.qMRMLNodeComboBox()
    self.__baselineVolumeSelector.toolTip = "Choose the baseline volume"
    self.__baselineVolumeSelector.nodeTypes = ['vtkMRMLScalarVolumeNode']
    self.__baselineVolumeSelector.setMRMLScene(slicer.mrmlScene)
    self.__baselineVolumeSelector.addEnabled = 0

    followupScanLabel = qt.QLabel( 'Followup volume:' )
    self.__followupVolumeSelector = slicer.qMRMLNodeComboBox()
    self.__followupVolumeSelector.toolTip = "Choose the followup volume"
    self.__followupVolumeSelector.nodeTypes = ['vtkMRMLScalarVolumeNode']
    self.__followupVolumeSelector.setMRMLScene(slicer.mrmlScene)
    self.__followupVolumeSelector.addEnabled = 0
   
    loadDataButton = qt.QPushButton('Load test data')
    self.__layout.addRow(loadDataButton)
    loadDataButton.connect('clicked()', self.loadTestData)

    self.__layout.addRow(baselineScanLabel, self.__baselineVolumeSelector)
    self.__layout.addRow(followupScanLabel, self.__followupVolumeSelector)

    self.updateWidgetFromParameters(self.parameterNode())

    qt.QTimer.singleShot(0, self.killButton)


  def killButton(self):
    # hide useless button
    bl = slicer.util.findChildren(text='Registration')
    if len(bl):
      bl[3].hide()
      

  def loadTestData(self):
    vl = slicer.modules.volumes.logic()
    vol1 = vl.AddArchetypeVolume('/home/mariana/thesis/volumes/first_batch/patient1-us1/test.dcm', 'volume1', 0)
    vol2 = vl.AddArchetypeVolume('/home/mariana/thesis/volumes/first_batch/patient1-us2/test.dcm', 'volume2', 0)
    if vol1 != None and vol2 != None:
      self.__baselineVolumeSelector.setCurrentNode(vol1)
      self.__followupVolumeSelector.setCurrentNode(vol2)
      self.setBgFgVolumes(vol1.GetID(), vol2.GetID())


  def validate(self, desiredBranchId):
    '''
    Must define it since we inherit from ctk.ctkWorkflowWidgetStep
    Check if the baseline and follow-up volumes have been chosen and if they are valid.
    '''
    self.__parent.validate(desiredBranchId)

    # Check that the selectors are not empty
    baseline = self.__baselineVolumeSelector.currentNode()
    followup = self.__followupVolumeSelector.currentNode()

    if baseline != None and followup != None:
      baselineID = baseline.GetID()
      followupID = followup.GetID()
      
      if baselineID != '' and followupID != '' and baselineID != followupID: #TODO Why check if they are the same?
        pNode = self.parameterNode()
        pNode.SetParameter('baselineVolumeID', baselineID)
        pNode.SetParameter('followupVolumeID', followupID)
        
        self.__parent.validationSucceeded(desiredBranchId)
      else:
        self.__parent.validationFailed(desiredBranchId, 'Error','Please select disctint baseline and followup volumes.')
    else:
      self.__parent.validationFailed(desiredBranchId, 'Error','Please select both baseline and followup volumes.')


  def onEntry(self, comingFrom, transitionType):
    super(SelectVolumesStep, self).onEntry(comingFrom, transitionType)
    
    self.updateWidgetFromParameters(self.parameterNode())
    pNode = self.parameterNode()
    pNode.SetParameter('currentStep', self.stepid)
    
    qt.QTimer.singleShot(0, self.killButton)


  def onExit(self, goingTo, transitionType):
    if goingTo.id() != 'Registration':
      return

    # Nothing more because we already saved the volumes in pNode during validation
    super(SelectVolumesStep, self).onExit(goingTo, transitionType)

  
  def updateWidgetFromParameters(self, parameterNode):
    '''
    Update the widget according to the parameters selected by the user
    '''
    baselineVolumeID = parameterNode.GetParameter('baselineVolumeID')
    followupVolumeID = parameterNode.GetParameter('followupVolumeID')
    if baselineVolumeID != None:
      self.__baselineVolumeSelector.setCurrentNode(slicer.mrmlScene.GetNodeByID(baselineVolumeID))
    if followupVolumeID != None:
      self.__followupVolumeSelector.setCurrentNode(slicer.mrmlScene.GetNodeByID(followupVolumeID))


  def setBgFgVolumes(self, bg, fg): #TODO does Slicer already have a function for this?
    appLogic = slicer.app.applicationLogic()
    selectionNode = appLogic.GetSelectionNode()
    selectionNode.SetReferenceActiveVolumeID(bg)
    selectionNode.SetReferenceSecondaryVolumeID(fg)
    appLogic.PropagateVolumeSelection()