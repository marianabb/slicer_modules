from __main__ import qt, ctk, vtk, slicer

from MRIChangeDetectorStep import *


class QuantificationStep(MRIChangeDetectorStep):
  def __init__(self, stepid):
    self.initialize(stepid)
    self.setName( '3. Quantify and show the differences' )
    self.setDescription( 'Find small differences between the baseline and follow-up volumes.' )
    
    self.__parent = super(QuantificationStep, self)

    # Volume generated when the registered and the original volume are subtracted
    self.__subtractedVolume = None

    qt.QTimer.singleShot(0, self.killButton)


  def createUserInterface(self):
    '''
    Initially just a button for quantification.
    '''

    self.__layout = self.__parent.createUserInterface()

    # Quantification button
    self.__quantificationButton = qt.QPushButton("Run quantification")
    self.__quantificationButton.toolTip = "Measure the differences between baseline and follow-up volumes."
    self.__quantificationStatus = qt.QLabel('Quantification Status: N/A')

    
    self.__layout.addRow(self.__quantificationButton)
    self.__layout.addRow("", qt.QWidget()) # empty row
    self.__layout.addRow(self.__quantificationStatus)
    self.__layout.addRow("", qt.QWidget()) # empty row
    self.__quantificationButton.connect('clicked()', self.onQuantificationRequest)

    qt.QTimer.singleShot(0, self.killButton)


  def killButton(self):
    # hide useless button
    bl = slicer.util.findChildren(text='Quantification')
    if len(bl):
      bl[2].hide()
    

  def onEntry(self, comingFrom, transitionType):
    super(QuantificationStep, self).onEntry(comingFrom, transitionType)
    
    self.updateWidgetFromParameters(self.parameterNode())
    pNode = self.parameterNode()
    pNode.SetParameter('currentStep', self.stepid)

    qt.QTimer.singleShot(0, self.killButton)
    
    
  def onExit(self, goingTo, transitionType):
    if goingTo.id() != 'Quantification':
      return

    # Nothing more because we already saved the volumes in pNode during validation
    super(SelectVolumesStep, self).onExit(goingTo, transitionType)


  def updateWidgetFromParameters(self, parameterNode):
    '''
    Update the widget according to the parameters selected by the user
    '''
    pass #TODO: Delete if useless


  def validate(self, desiredBranchId):
    '''
    Must define it since we inherit from ctk.ctkWorkflowWidgetStep
    '''
    self.__parent.validate(desiredBranchId)
    

  def onQuantificationRequest(self):
    # TODO: Validate inputs? (there are no inputs so far)
    
    # Obtain inputs
    pNode = self.parameterNode()
    baselineVolumeID = pNode.GetParameter('baselineVolumeID')
    registeredVolumeID = pNode.GetParameter('followupRegisteredVolumeID')

    # Subtract baseline and registered volumes. Result in self.__subtractedVolume
    self.subtractVolumes(baselineVolumeID, registeredVolumeID)
    


  def subtractVolumes(self, IDvol1, IDvol2):
    subtractmodule = slicer.modules.subtractscalarvolumes
    
    # Fill in the parameters
    parameters = {}
    parameters["inputVolume1"] = IDvol1
    parameters["inputVolume2"] = IDvol2
    
    # Create an output volume
    self.__subtractedVolume = slicer.mrmlScene.CreateNodeByClass('vtkMRMLScalarVolumeNode')
    slicer.mrmlScene.AddNode(self.__subtractedVolume)
    parameters["outputVolume"] = self.__subtractedVolume.GetID()
    
    self.__cliNode = None
    self.__cliNode = slicer.cli.run(subtractmodule, self.__cliNode, parameters)

    # Each time the event is modified, the function processSubtractCompletion will be called.
    self.__cliObserverTag = self.__cliNode.AddObserver('ModifiedEvent', self.processSubtractCompletion)
    self.__quantificationStatus.setText('Subtracting volumes...')
    self.__quantificationButton.setEnabled(0)


  def processSubtractCompletion(self, node, event):
    status = node.GetStatusString()
    self.__quantificationStatus.setText('Subtract status: '+status)

    if status == 'Completed':
      self.__quantificationButton.setEnabled(1)
      
      # Save result in pNode
      pNode = self.parameterNode()
      pNode.SetParameter('subtractedVolumeID', self.__subtractedVolume.GetID())
      
      # Get data from the volume
      #i = self.__subtractedVolume.GetImageData()
      #import vtk.util.numpy_support
      #a = vtk.util.numpy_support.vtk_to_numpy(i.GetPointData().GetScalars())

    elif status == 'CompletedWithErrors':
      self.__quantificationButton.setEnabled(1)
      qt.QMessageBox.warning(self, 'Error: Subtract', 'Subtract completed with errors.')
