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
    # Label map from the subtracted volume
    self.__labelMap = None

    qt.QTimer.singleShot(0, self.killButton)


  def createUserInterface(self):
    '''
    Initially just a button for quantification.
    '''

    self.__layout = self.__parent.createUserInterface()

    # Threshold range widget
    threshLabel = qt.QLabel('Choose threshold:')
    self.__threshRange = slicer.qMRMLRangeWidget()
    self.__threshRange.decimals = 0
    self.__threshRange.singleStep = 1
    self.__threshRange.maximum = 255.0
    self.__threshRange.minimumValue = 60
    self.__threshRange.maximumValue = 255

    self.__layout.addRow(threshLabel)
    self.__layout.addRow(self.__threshRange)
    self.__layout.addRow("", qt.QWidget()) # empty row


    # Quantification button
    self.__quantificationButton = qt.QPushButton("Run quantification")
    self.__quantificationButton.toolTip = "Measure the differences between baseline and follow-up volumes."
    self.__quantificationStatus = qt.QLabel('Quantification Status: N/A')

    self.__layout.addRow(self.__quantificationButton)
    self.__layout.addRow("", qt.QWidget()) # empty row
    self.__layout.addRow(self.__quantificationStatus)
    self.__layout.addRow("", qt.QWidget()) # empty row
    self.__quantificationButton.connect('clicked()', self.onQuantificationRequest)
    self.__layout.addRow("", qt.QWidget()) # empty row

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
    # Nothing more because we already saved the volumes in pNode during validation
    super(QuantificationStep, self).onExit(goingTo, transitionType)


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
    

    # pop up progress dialog to prevent user from messing around
    self.progress = qt.QProgressDialog(slicer.util.mainWindow())
    self.progress.minimumDuration = 0
    self.progress.show()
    self.progress.setValue(0) # Set first step
    self.progress.setMaximum(2) # Total number of steps
    self.progress.setCancelButton(0)
    self.progress.setWindowModality(2)
 
    self.progress.setLabelText('Subtracting baseline volume and registered follow-up volume')
    slicer.app.processEvents(qt.QEventLoop.ExcludeUserInputEvents)
    self.progress.repaint()

    pNode = self.parameterNode()

    
    # 1. Subtract baseline and registered volumes. Result in self.__subtractedVolume
    # Only subtract if I haven't done it before
    if pNode.GetParameter('subtractedVolumeID') == '':
      self.__quantificationStatus.setText('Subtracting volumes...')
      self.__quantificationButton.setEnabled(0)

      # Obtain inputs
      baselineVolumeID = pNode.GetParameter('baselineVolumeID')
      registeredVolumeID = pNode.GetParameter('registeredVolumeID')

      subtractmodule = slicer.modules.subtractscalarvolumes
    
      # Fill in the parameters
      parameters = {}
      parameters["inputVolume1"] = baselineVolumeID
      parameters["inputVolume2"] = registeredVolumeID
    
      # Create an output volume
      self.__subtractedVolume = slicer.mrmlScene.CreateNodeByClass('vtkMRMLScalarVolumeNode')
      self.__subtractedVolume.SetName('Subtract_output')
      slicer.mrmlScene.AddNode(self.__subtractedVolume)
      parameters["outputVolume"] = self.__subtractedVolume.GetID()
    

      self.__cliNode = None
      self.__cliNode = slicer.cli.run(subtractmodule, self.__cliNode, parameters, wait_for_completion = True)

      status = self.__cliNode.GetStatusString()
      if status == 'Completed':
        self.__quantificationStatus.setText('Subtract status: '+status)
        
        # Change color of the volume to something brighter
        labelsColorNode = slicer.modules.colors.logic().GetColorTableNodeID(20) # ColorTable Magenta
        self.__subtractedVolume.GetDisplayNode().SetAndObserveColorNodeID(labelsColorNode)
     
        # Create a LabelMap with the subtraction volume
        self.__labelMap = slicer.mrmlScene.CreateNodeByClass('vtkMRMLLabelMapVolumeDisplayNode')
        self.__labelMap.SetName('Subtract_LabelMap')
        slicer.mrmlScene.AddNode(self.__labelMap)
 
        # Save result in pNode
        pNode = self.parameterNode()
        pNode.SetParameter('subtractedVolumeID', self.__subtractedVolume.GetID())
        pNode.SetParameter('subtractionLabelMap', self.__labelMap.GetID())

        # Get data from the volume
        #i = self.__subtractedVolume.GetImageData()
        #a = vtk.util.numpy_support.vtk_to_numpy(i.GetPointData().GetScalars())

      
      elif status == 'CompletedWithErrors' or status == 'Idle':
        self.__quantificationStatus.setText('Subtract status: '+status)
        self.__quantificationButton.setEnabled(1)
        #qt.QMessageBox.warning(self, 'Error: Subtract', 'Subtract completed with errors.')
      
        # close the progress window 
        self.progress.setValue(2)
        self.progress.repaint()
        slicer.app.processEvents(qt.QEventLoop.ExcludeUserInputEvents)
        self.progress.close() #TODO: Think this case further
        self.progress = None


    # update the progress window 
    self.progress.setValue(1)
    self.progress.setLabelText('Rendering volume')
    slicer.app.processEvents(qt.QEventLoop.ExcludeUserInputEvents)
    self.progress.repaint()

    # 2. Create a volume with the differences
    self.__quantificationStatus.setText('Rendering volume...')

            
    # close the progress window 
    self.progress.setValue(2)
    self.progress.repaint()
    slicer.app.processEvents(qt.QEventLoop.ExcludeUserInputEvents)
    self.progress.close()
    self.progress = None
    
    # Enable the button again
    self.__quantificationButton.setEnabled(1)
    self.__quantificationStatus.setText('Rendering done.')
 
