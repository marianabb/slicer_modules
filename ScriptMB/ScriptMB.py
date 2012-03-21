from __main__ import vtk, qt, ctk, slicer

#
# ScriptMB
#

class ScriptMB:
  def __init__(self, parent):
    parent.title = "Scripted Loadable Extension"
    parent.categories = ["Mariana"]
    parent.dependencies = []
    parent.contributors = ["Mariana Bustamante (Uppsala University)"]
    parent.helpText = """
    First scripted loadable extension.
    """
    parent.acknowledgementText = """
    This file was originally developed by Mariana Bustamante, Uppsala University.
    """
    self.parent = parent

#
# qScriptMBWidget
#

class ScriptMBWidget:
  def __init__(self, parent = None):
    if not parent:
      self.parent = slicer.qMRMLWidget()
      self.parent.setLayout(qt.QVBoxLayout())
      self.parent.setMRMLScene(slicer.mrmlScene)
    else:
      self.parent = parent
    self.layout = self.parent.layout()
    if not parent:
      self.setup()
      self.parent.show()

  def setup(self):
    # Instantiate and connect widgets ...
    
    # Collapsible button
    __collapsibleButton = ctk.ctkCollapsibleButton()
    __collapsibleButton.text = "A collapsible tab"
    self.layout.addWidget(__collapsibleButton)

    # Layout within the collapsible button
    __formLayout = qt.QFormLayout(__collapsibleButton)

    # Fixed Volume Selector
    __fixedVolumeSelector = slicer.qMRMLNodeComboBox()
    __fixedVolumeSelector.objectName = 'fixedVolumeSelector'
    __fixedVolumeSelector.toolTip = "The fixed image for registration."
    __fixedVolumeSelector.nodeTypes = ['vtkMRMLVolumeNode']
    __fixedVolumeSelector.noneEnabled = True
    __fixedVolumeSelector.addEnabled = False
    __fixedVolumeSelector.removeEnabled = False
    __formLayout.addRow("Fixed Volume:", __fixedVolumeSelector)
    self.parent.connect('mrmlSceneChanged(vtkMRMLScene*)', __fixedVolumeSelector, 'setMRMLScene(vtkMRMLScene*)')

    # Moving Volume Selector
    __movingVolumeSelector = slicer.qMRMLNodeComboBox()
    __movingVolumeSelector.objectName = 'movingVolumeSelector'
    __movingVolumeSelector.toolTip = "The moving image for registration."
    __movingVolumeSelector.nodeTypes = ['vtkMRMLVolumeNode']
    __movingVolumeSelector.noneEnabled = True
    __movingVolumeSelector.addEnabled = False
    __movingVolumeSelector.removeEnabled = False
    __formLayout.addRow("Moving Volume:", __movingVolumeSelector)
    self.parent.connect('mrmlSceneChanged(vtkMRMLScene*)', __movingVolumeSelector, 'setMRMLScene(vtkMRMLScene*)')
    

    # Register button
    __registerButton = qt.QPushButton("Register volumes")
    __registerButton.toolTip = "Register the volumes."
    __registerStatus = qt.QLabel('Register volumes')
    __formLayout.addRow(__registerStatus, __registerButton)
    __registerButton.connect('clicked(bool)', self.onRegisterButtonClicked)

    # Subtract button
    __subtractButton = qt.QPushButton("Subtract volumes")
    __subtractButton.toolTip = "Subtract the volumes."
    __subtractStatus = qt.QLabel('Subtract volumes')
    __formLayout.addRow(__subtractStatus, __subtractButton)
    __subtractButton.connect('clicked(bool)', self.onSubtractButtonClicked)
    
    
    # Add vertical spacer
    self.layout.addStretch(1)

    # Set local var as instance attribute
    self.__fixedVolumeSelector = __fixedVolumeSelector
    self.__movingVolumeSelector = __movingVolumeSelector
    self.__registerButton = __registerButton
    self.__registerStatus = __registerStatus
    self.__subtractButton = __subtractButton
    self.__subtractStatus = __subtractStatus
   

  def onRegisterButtonClicked(self):
    scene = slicer.mrmlScene
    
    fixedVolume = self.__fixedVolumeSelector.currentNode()
    movingVolume = self.__movingVolumeSelector.currentNode()
    
    brainsWarp = slicer.modules.brainsdemonwarp # takes forever!
    brainsFit = slicer.modules.brainsfit # Tested during Image Analysis II. Takes about 20mins
    bsplinedeformable = slicer.modules.bsplinedeformableregistration # Tested during Image Analysis II
    
    parameters = {}
    # TODO remove the automatic loading and leave this one
    #parameters["movingVolume"] = movingVolume.GetID()
    #parameters["fixedVolume"] = fixedVolume.GetID()

    # Only for testing. Load volumes automatically
    # TODO Remove when out of testing
    vols = self.loadVolumesForTesting()
    fixedVolume = vols["fixedVolume"]
    movingVolume = vols["movingVolume"]
    parameters["movingVolume"] = movingVolume
    parameters["fixedVolume"] = fixedVolume

    # ONLY for brainsfit
    parameters['initializeTransformMode'] = 'useCenterOfHeadAlign'
    parameters['useRigid'] = True
    
    # Create an output volume
    outputVolume = slicer.vtkMRMLScalarVolumeNode()
    outputVolume.SetModifiedSinceRead(1)
    
    outputVolume.SetName('registered_volume')
   
    scene.AddNode(outputVolume) # Important before GetID()!
    parameters["outputVolume"] = outputVolume.GetID()

    print "Calling register volumes CLI..."
    self.__cliNode = None
    self.__cliNode = slicer.cli.run(brainsFit, self.__cliNode, parameters)
    
    # Each time the event is modified, the function processSubtractCompletion will be called.
    self.__cliObserverTag = self.__cliNode.AddObserver('ModifiedEvent', self.processRegistrationCompletion)
    self.__registerStatus.setText('Wait ...')
    self.__registerButton.setEnabled(0)


  def processRegistrationCompletion(self, node, event):
    status = node.GetStatusString()
    self.__registerStatus.setText('Registration '+status)

    if status == 'Completed':
      print "Register volumes CLI finished!!"
      self.__registerButton.setEnabled(1)
      
    
    
  def onSubtractButtonClicked(self):
    scene = slicer.mrmlScene
    subtractmodule = slicer.modules.subtractscalarvolumes

    vols = self.loadVolumesForTesting()
    fixedVolume = vols["fixedVolume"]
    movingVolume = vols["movingVolume"]
    
    parameters = {}
    parameters["inputVolume1"] = fixedVolume
    parameters["inputVolume2"] = movingVolume

    outputVolume = slicer.vtkMRMLScalarVolumeNode()
    outputVolume.SetModifiedSinceRead(1)
    outputVolume.SetName('subtracted_volume')
    scene.AddNode(outputVolume) # Important before GetID()!
    
    parameters["outputVolume"] = outputVolume.GetID()

    print "Calling subtract volumes CLI..."
    self.__cliNode = None
    self.__cliNode = slicer.cli.run(subtractmodule, self.__cliNode, parameters)

    # Each time the event is modified, the function processSubtractCompletion will be called.
    self.__cliObserverTag = self.__cliNode.AddObserver('ModifiedEvent', self.processSubtractCompletion)
    self.__subtractStatus.setText('Wait ...')
    self.__subtractButton.setEnabled(0)


  def processSubtractCompletion(self, node, event):
    status = node.GetStatusString()
    self.__subtractStatus.setText('Subtract '+status)

    if status == 'Completed':
      print "Subtract volumes CLI finished!!"
      self.__subtractButton.setEnabled(1)
      

      
  def loadVolumesForTesting(self):
    fixedV = slicer.util.loadVolume("/home/mariana/thesis/volumes/first_batch/patient1-us1/test.dcm")
    movingV = slicer.util.loadVolume("/home/mariana/thesis/volumes/first_batch/patient1-us2/test.dcm")

    fixedN = getNode('test')
    movingN = getNode('test_1')

    volumes = {}
    volumes["fixedVolume"] = fixedN
    volumes["movingVolume"] = movingN

    return volumes
    