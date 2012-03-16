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
    dummyCollapsibleButton = ctk.ctkCollapsibleButton()
    dummyCollapsibleButton.text = "A collapsible tab"
    self.layout.addWidget(dummyCollapsibleButton)

    # Layout within the dummy collapsible button
    dummyFormLayout = qt.QFormLayout(dummyCollapsibleButton)

    # GrayModel button
    grayModelButton = qt.QPushButton("Gray Scale Model Maker")
    grayModelButton.toolTip = "Apply the module 'Gray Scale Model Maker' on the volume MRHead. MRHead shoudl be already loaded."
    dummyFormLayout.addWidget(grayModelButton)
    grayModelButton.connect('clicked(bool)', self.onGrayModelButtonClicked)

    # Fixed Volume Selector
    fixedVolumeSelector = slicer.qMRMLNodeComboBox()
    fixedVolumeSelector.objectName = 'fixedVolumeSelector'
    fixedVolumeSelector.toolTip = "The fixed image for registration."
    fixedVolumeSelector.nodeTypes = ['vtkMRMLVolumeNode']
    fixedVolumeSelector.noneEnabled = True
    fixedVolumeSelector.addEnabled = False
    fixedVolumeSelector.removeEnabled = False
    #fixedVolumeSelector.connect('currentNodeChanged(bool)', self.enableOrDisableCreateButton)
    dummyFormLayout.addRow("Fixed Volume:", fixedVolumeSelector)
    self.parent.connect('mrmlSceneChanged(vtkMRMLScene*)', fixedVolumeSelector, 'setMRMLScene(vtkMRMLScene*)')

    # Moving Volume Selector
    movingVolumeSelector = slicer.qMRMLNodeComboBox()
    movingVolumeSelector.objectName = 'movingVolumeSelector'
    movingVolumeSelector.toolTip = "The moving image for registration."
    movingVolumeSelector.nodeTypes = ['vtkMRMLVolumeNode']
    movingVolumeSelector.noneEnabled = True
    movingVolumeSelector.addEnabled = False
    movingVolumeSelector.removeEnabled = False
    #movingVolumeSelector.connect('currentNodeChanged(bool)', self.enableOrDisableCreateButton)
    dummyFormLayout.addRow("Moving Volume:", movingVolumeSelector)
    self.parent.connect('mrmlSceneChanged(vtkMRMLScene*)', movingVolumeSelector, 'setMRMLScene(vtkMRMLScene*)')
    

    # Register button
    registerButton = qt.QPushButton("Register")
    registerButton.toolTip = "Register the volumes."
    dummyFormLayout.addWidget(registerButton)
    registerButton.connect('clicked(bool)', self.onRegisterButtonClicked)
    
    
    # Add vertical spacer
    self.layout.addStretch(1)

    # Set local var as instance attribute
    self.grayModelButton = grayModelButton
    self.fixedVolumeSelector = fixedVolumeSelector
    self.movingVolumeSelector = movingVolumeSelector
    self.registerButton = registerButton
    

  def onGrayModelButtonClicked(self):
    #slicer.util.loadVolume("/home/mariana/thesis/volumes/first_batch/patient1-us1/test.dcm")
    # Once loaded, obtain the Node
    n = getNode('MRHead')
    parameters = {}
    parameters["InputVolume"] = n.GetID()
    outModel = slicer.vtkMRMLModelNode()
    slicer.mrmlScene.AddNode( outModel )
    parameters["OutputGeometry"] = outModel.GetID()

    parameters["Threshold"] = 70
    
    grayMaker = slicer.modules.grayscalemodelmaker
    slicer.cli.run(grayMaker, None, parameters)


  def onRegisterButtonClicked(self):
    fixedVolume = self.fixedVolumeSelector.currentNode()
    movingVolume = self.movingVolumeSelector.currentNode()
   
    brainsWarp = slicer.modules.brainsdemonwarp

   
    parameters = {}
    parameters["movingVolume"] = movingVolume.GetID()
    parameters["fixedVolume"] = fixedVolume.GetID()
    outputVolume = slicer.vtkMRMLModelNode()
    slicer.mrmlScene.AddNode(outputVolume)
    parameters["outputVolume"] = outputVolume.GetID()
   
    slicer.cli.run(brainsWarp, None, parameters)
   