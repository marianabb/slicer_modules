from __main__ import vtk, qt, ctk, slicer

import MRIChangeDetectorWizard

#
# MRIChangeDetector
#

class MRIChangeDetector:
  def __init__(self, parent):
    parent.title = "MRIChangeDetector"
    parent.categories = ["Uppsala"]
    parent.dependencies = []
    parent.contributors = ["Mariana Bustamante (Uppsala University)"]
    parent.helpText = """
    Registers two images and uses the result to quantify small differences between them.
    """
    parent.acknowledgementText = """
    This file was originally developed by Mariana Bustamante, Uppsala University.
    """ 
    self.parent = parent

#
# qMRIChangeDetectorWidget
#

class MRIChangeDetectorWidget:
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
    '''
    Define a workflow with the necessary steps.
    '''
    
    self.workflow = ctk.ctkWorkflow()
    
    workflowWidget = ctk.ctkWorkflowStackedWidget()
    workflowWidget.setWorkflow(self.workflow)

    workflowWidget.buttonBoxWidget().nextButtonDefaultText = ""
    workflowWidget.buttonBoxWidget().backButtonDefaultText = ""
    
    # Create all wizard steps
    selectVolumesStep = MRIChangeDetectorWizard.SelectVolumesStep('SelectVolumes')
    registrationStep = MRIChangeDetectorWizard.RegistrationStep('Registration')
    quantificationStep = MRIChangeDetectorWizard.QuantificationStep('Quantification')

    # add the wizard steps to an array for convenience
    allSteps = []

    allSteps.append(selectVolumesStep)
    allSteps.append(registrationStep)
    allSteps.append(quantificationStep)

    # Add transition for the first step which let's the user choose between simple and advanced mode
    self.workflow.addTransition( selectVolumesStep, registrationStep)
    self.workflow.addTransition( registrationStep, quantificationStep)

    nNodes = slicer.mrmlScene.GetNumberOfNodesByClass('vtkMRMLScriptedModuleNode')

    self.parameterNode = None
    for n in xrange(nNodes):
      compNode = slicer.mrmlScene.GetNthNodeByClass(n, 'vtkMRMLScriptedModuleNode')
      nodeid = None
      if compNode.GetModuleName() == 'MRIChangeDetector':
        self.parameterNode = compNode
        print 'Found existing MRIChangeDetector parameter node'
        break
    if self.parameterNode == None:
      self.parameterNode = slicer.mrmlScene.CreateNodeByClass('vtkMRMLScriptedModuleNode')
      self.parameterNode.SetModuleName('MRIChangeDetector')
      slicer.mrmlScene.AddNode(self.parameterNode)
 
    # Propagate the workflow, the logic and the MRML Manager to the steps
    for s in allSteps:
        s.setWorkflow(self.workflow)
        s.setParameterNode(self.parameterNode)

    # restore workflow step
    currentStep = self.parameterNode.GetParameter('currentStep')
    if currentStep != '':
      print 'Restoring workflow step to ', currentStep
      if currentStep == 'SelectVolumes':
        self.workflow.setInitialStep(selectVolumesStep)
      if currentStep == 'Registration':
        self.workflow.setInitialStep(registrationStep)
      if currentStep == 'Quantification':
        self.workflow.setInitialStep(quantificationStep)
    else:
      print 'currentStep in parameter node is empty!'
        
    # start the workflow and show the widget
    self.workflow.start()
    workflowWidget.visible = True
    self.layout.addWidget(workflowWidget)


    
  def enter(self):
    print "MRIChangeDetector: enter() called"
