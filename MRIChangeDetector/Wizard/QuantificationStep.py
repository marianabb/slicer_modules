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
    # Volume generated after thresholding the subtracted volume
    self.__thresholdedVolume = None

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

    # Volume rendering test button
    self.__testButton = qt.QPushButton("Run volume!")
    self.__testButton.toolTip = ""
    self.__testStatus = qt.QLabel('Volume Status: N/A')

    self.__layout.addRow(self.__quantificationButton)
    self.__layout.addRow("", qt.QWidget()) # empty row
    self.__layout.addRow(self.__quantificationStatus)
    self.__layout.addRow("", qt.QWidget()) # empty row
    self.__quantificationButton.connect('clicked()', self.onQuantificationRequest)

    self.__layout.addRow(self.__testButton)
    self.__layout.addRow("", qt.QWidget()) # empty row
    self.__layout.addRow(self.__testStatus)
    self.__layout.addRow("", qt.QWidget()) # empty row
    self.__testButton.connect('clicked()', self.onTestRequest)


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
    
    self.__quantificationStatus.setText('Subtracting volumes...')
    self.__quantificationButton.setEnabled(0)

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

    
    # Obtain inputs
    pNode = self.parameterNode()
    baselineVolumeID = pNode.GetParameter('baselineVolumeID')
    registeredVolumeID = pNode.GetParameter('registeredVolumeID')

    # 1. Subtract baseline and registered volumes. Result in self.__subtractedVolume
    subtractmodule = slicer.modules.subtractscalarvolumes
    
    # Fill in the parameters
    parameters = {}
    parameters["inputVolume1"] = baselineVolumeID
    parameters["inputVolume2"] = registeredVolumeID
    
    # Create an output volume
    self.__subtractedVolume = slicer.mrmlScene.CreateNodeByClass('vtkMRMLScalarVolumeNode')
    slicer.mrmlScene.AddNode(self.__subtractedVolume)
    parameters["outputVolume"] = self.__subtractedVolume.GetID()
    

    self.__cliNode = None
    self.__cliNode = slicer.cli.run(subtractmodule, self.__cliNode, parameters, wait_for_completion = True)

    status = self.__cliNode.GetStatusString()
    if status == 'Completed':
      self.__quantificationStatus.setText('Subtract status: '+status)
      #self.__quantificationButton.setEnabled(1) # TODO move to a better place
      
      # Save result in pNode
      pNode = self.parameterNode()
      pNode.SetParameter('subtractedVolumeID', self.__subtractedVolume.GetID())
      
      # Get data from the volume
      #i = self.__subtractedVolume.GetImageData()
      #a = vtk.util.numpy_support.vtk_to_numpy(i.GetPointData().GetScalars())

      # close the progress window 
      self.progress.setValue(1)
      self.progress.repaint()
      slicer.app.processEvents(qt.QEventLoop.ExcludeUserInputEvents)
      
    elif status == 'CompletedWithErrors' or status == 'Idle':
      self.__quantificationStatus.setText('Subtract status: '+status)
      self.__quantificationButton.setEnabled(1)
      #qt.QMessageBox.warning(self, 'Error: Subtract', 'Subtract completed with errors.')
      
      # close the progress window 
      self.progress.setValue(1)
      self.progress.repaint()
      slicer.app.processEvents(qt.QEventLoop.ExcludeUserInputEvents)
      self.progress.close() #TODO: Think this case further
      self.progress = None


    # 2. Threshold the subtracted volume to highlight only differences
    self.progress.setLabelText('Thresholding subtracted volume')
    slicer.app.processEvents(qt.QEventLoop.ExcludeUserInputEvents)
    self.progress.repaint()

    thresholdmodule = slicer.modules.thresholdscalarvolume

    # Fill in the parameters
    parameters = {}
    parameters["InputVolume"] = self.__subtractedVolume.GetID()
    parameters["ThresholdValue"] = 60 # TODO: User should select this
    parameters["OutsideValue"] = 255
    parameters["ThresholdType"] = "Above"

    # Create an output volume
    self.__thresholdedVolume = slicer.mrmlScene.CreateNodeByClass('vtkMRMLScalarVolumeNode')
    slicer.mrmlScene.AddNode(self.__thresholdedVolume)
    parameters["OutputVolume"] = self.__thresholdedVolume.GetID()

    self.__cliNode = None
    self.__cliNode = slicer.cli.run(thresholdmodule, self.__cliNode, parameters, wait_for_completion = True)

    status = self.__cliNode.GetStatusString()
    if status == 'Completed':
      self.__quantificationStatus.setText('Thresholding status: '+status)
      self.__quantificationButton.setEnabled(1) # TODO move to final step
      
      # Save result in pNode
      pNode = self.parameterNode()
      pNode.SetParameter('thresholdedVolumeID', self.__thresholdedVolume.GetID())

      # close the progress window 
      self.progress.setValue(2)
      self.progress.repaint()
      slicer.app.processEvents(qt.QEventLoop.ExcludeUserInputEvents)
      self.progress.close()
      self.progress = None
      
    elif status == 'CompletedWithErrors':
      self.__quantificationStatus.setText('Thresholding status: '+status)
      self.__quantificationButton.setEnabled(1)
            
      # close the progress window 
      self.progress.setValue(2)
      self.progress.repaint()
      slicer.app.processEvents(qt.QEventLoop.ExcludeUserInputEvents)
      self.progress.close()
      self.progress = None





  def onTestRequest(self):
    # 3. VR Testing

    pNode = self.parameterNode()

    self.__vrLogic = None
    self.__vrDisplayNode = None

    self.__vrLogic = slicer.modules.volumerendering.logic() # createUserInterface

    # create VR node first time a valid ROI is selected (onROIChanged)
    if self.__vrDisplayNode == None:
      self.__vrDisplayNode = self.__vrLogic.CreateVolumeRenderingDisplayNode()
      viewNode = slicer.util.getNode('vtkMRMLViewNode1')
      self.__vrDisplayNode.SetCurrentVolumeMapper(0)
      self.__vrDisplayNode.AddViewNodeID(viewNode.GetID())
      
      v = slicer.mrmlScene.GetNodeByID(pNode.GetParameter('subtractedVolumeID'))
      self.__vrDisplayNode.SetAndObserveVolumeNodeID(v.GetID())
      self.__vrLogic.UpdateDisplayNodeFromVolumeNode(self.__vrDisplayNode, v)
      self.__vrOpacityMap = self.__vrDisplayNode.GetVolumePropertyNode().GetVolumeProperty().GetScalarOpacity()
      self.__vrColorMap = self.__vrDisplayNode.GetVolumePropertyNode().GetVolumeProperty().GetRGBTransferFunction()
      
      # setup color transfer function once
      # baselineROIRange = v.GetImageData().GetScalarRange()

      # self.__vrColorMap.RemoveAllPoints()
      # self.__vrColorMap.AddRGBPoint(0, 0, 0, 0)
      # self.__vrColorMap.AddRGBPoint(baselineROIRange[0]-1, 0, 0, 0) 
      # self.__vrColorMap.AddRGBPoint(baselineROIRange[0], 0.8, 0.8, 0) 
      # self.__vrColorMap.AddRGBPoint(baselineROIRange[1], 0.8, 0.8, 0) 
      # self.__vrColorMap.AddRGBPoint(baselineROIRange[1]+1, 0, 0, 0) 

      self.__vrDisplayNode.VisibilityOn()

      threshRange = [60, 255]
      self.__vrOpacityMap.RemoveAllPoints()
      self.__vrOpacityMap.AddPoint(0,0)
      self.__vrOpacityMap.AddPoint(0,0)
      self.__vrOpacityMap.AddPoint(threshRange[0]-1,0)
      self.__vrOpacityMap.AddPoint(threshRange[0],1)
      self.__vrOpacityMap.AddPoint(threshRange[1],1)
      self.__vrOpacityMap.AddPoint(threshRange[1]+1,0)
