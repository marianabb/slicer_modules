from __main__ import qt, ctk, vtk, slicer

from TMRIChangeDetectorStep import *


class QuantificationStep(TMRIChangeDetectorStep):
  def __init__(self, stepid):
    self.initialize(stepid)
    self.setName( '3. Quantify and show the differences' )
    self.setDescription( 'Find differences between the baseline and follow-up volumes according to the deformation field.' )
    
    self.__parent = super(QuantificationStep, self)

    # Label map from the Jacobians of the deformation field
    self.__outputLabelM = None
    self.__outputVolume = None

    qt.QTimer.singleShot(0, self.killButton)


  def createUserInterface(self):
    '''
    Initially just a button for quantification.
    '''

    self.__layout = self.__parent.createUserInterface()

    jacMinLabel = qt.QLabel('Choose the percentage of shrinkage to show in the output (green):')

    # MinJac SpinBox
    self.__minBox = qt.QDoubleSpinBox()
    self.__minBox.setValue(50.0) #Default min percentage
    self.__layout.addRow(jacMinLabel)
    self.__layout.addRow(self.__minBox)
    self.__layout.addRow("", qt.QWidget()) # empty row
    
    jacMaxLabel = qt.QLabel('Choose the percentage of growth to show in the output (pink):')

    # MaxJac SpinBox
    self.__maxBox = qt.QDoubleSpinBox()
    self.__maxBox.setValue(60.0) #Default max percentage
    self.__layout.addRow(jacMaxLabel)
    self.__layout.addRow(self.__maxBox)
    self.__layout.addRow("", qt.QWidget()) # empty row


    # Quantification button
    self.__quantificationButton = qt.QPushButton("Run tensor measurements")
    self.__quantificationButton.toolTip = "Measure the differences between baseline and follow-up volumes."
    self.__quantificationStatus = qt.QLabel('Measurement Status: N/A')

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
    pass


  def validate(self, desiredBranchId):
    '''
    Must define it since we inherit from ctk.ctkWorkflowWidgetStep
    '''
    self.__parent.validate(desiredBranchId)
    

  def onQuantificationRequest(self):
    # No validation of inputs since the percentages are checked by the QDoubleSpinBox(es)
    
    self.__quantificationStatus.setText('Measurement status: Running...')

    # pop up progress dialog to prevent user from messing around
    self.progress = qt.QProgressDialog(slicer.util.mainWindow())
    self.progress.minimumDuration = 0
    self.progress.show()
    self.progress.setValue(1) # Set first step
    self.progress.setMaximum(3) # Total number of steps
    self.progress.setCancelButton(0)
    self.progress.setWindowModality(2)
 
    self.progress.setLabelText('Calculating Jacobian determinants...')
    slicer.app.processEvents(qt.QEventLoop.ExcludeUserInputEvents)
    self.progress.repaint()

    pNode = self.parameterNode()

    
    # 1. Calculate Jacobian determinants and use the. Result in self.__outputLabelM
    # Only subtract if I haven't done it before
    #if pNode.GetParameter('jacobianLabelMapID') == '':
    self.__quantificationStatus.setText('Measuring deformation field...')
    self.__quantificationButton.setEnabled(0)

      # Obtain inputs
    baselineVolumeID = pNode.GetParameter('baselineVolumeID')
    registeredTransformID = pNode.GetParameter('registeredTransformID')
    
      # Fill in the parameters
    parameters = {}
    parameters["fixedVolume"] = baselineVolumeID
    parameters["deformationField"] = registeredTransformID
    parameters["minJac"] = self.__minBox.value
    parameters["maxJac"] = self.__maxBox.value
    
      # Create an output labelMap
    vl = slicer.modules.volumes.logic()
    baselineVolume = slicer.mrmlScene.GetNodeByID(pNode.GetParameter('baselineVolumeID'))
    self.__outputLabelM = vl.CreateLabelVolume(slicer.mrmlScene, baselineVolume, 'jacobianLabelMap')
    parameters["outputLabelMap"] = self.__outputLabelM.GetID()
    
    # Create an output volume
    vl = slicer.modules.volumes.logic()
    baselinevolume = slicer.mrmlScene.GetNodeByID(pNode.GetParameter('baselineVolumeID'))
    self.__outputVolume = vl.CloneVolume(slicer.mrmlScene, baselineVolume, 'jacobianVolume')
    parameters["outputVolume"] = self.__outputVolume.GetID()
    
    # Obtain the module from the moduleManager
    moduleManager = slicer.app.moduleManager()
    tensorModule = moduleManager.module('Tensor')
    
    # Call the module
    self.__cliNode = None
    self.__cliNode = slicer.cli.run(tensorModule, self.__cliNode, parameters, wait_for_completion = True)

    status = self.__cliNode.GetStatusString()
    if status == 'Completed':
      self.__quantificationStatus.setText('Measurement status: '+status)
      
      # update the progress window 
      self.progress.setValue(2)
      self.progress.setLabelText('Measurement Done. Creating LabelMap...')
      slicer.app.processEvents(qt.QEventLoop.ExcludeUserInputEvents)
      self.progress.repaint()
      
      # Change color of the labelMap to Labels
      labelsColorNode = slicer.modules.colors.logic().GetColorTableNodeID(10) # ColorTable Labels
      self.__outputLabelM.GetDisplayNode().SetAndObserveColorNodeID(labelsColorNode)
      
      # Save results in pNode
      pNode = self.parameterNode()
      pNode.SetParameter('jacobianLabelMapID', self.__outputLabelM.GetID())
      pNode.SetParameter('outputVolumeID', self.__outputVolume.GetID())
      
      # Place the useful things in Bg and Fg
      self.setBgFgVolumes(pNode.GetParameter('baselineVolumeID'), pNode.GetParameter('outputVolumeID'))
        

    elif status == 'CompletedWithErrors' or status == 'Idle':
      self.__quantificationStatus.setText('Measurement status: '+status)
      self.__quantificationButton.setEnabled(1)

         
    # close the progress window 
    self.progress.setValue(3)
    self.progress.repaint()
    slicer.app.processEvents(qt.QEventLoop.ExcludeUserInputEvents)
    self.progress.close()
    self.progress = None
    
    # Enable the button again
    self.__quantificationButton.setEnabled(1)
    self.__quantificationStatus.setText('Measurement status: Done. LabelMap created.')
 


  def setBgFgVolumes(self, bg, fg):
    appLogic = slicer.app.applicationLogic()
    selectionNode = appLogic.GetSelectionNode()
    selectionNode.SetReferenceActiveVolumeID(bg)
    selectionNode.SetReferenceSecondaryVolumeID(fg)
    appLogic.PropagateVolumeSelection()
