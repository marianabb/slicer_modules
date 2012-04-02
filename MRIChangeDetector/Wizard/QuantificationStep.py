from __main__ import qt, ctk, vtk, slicer

from MRIChangeDetectorStep import *


class QuantificationStep(MRIChangeDetectorStep):
  def __init__(self, stepid):
    self.initialize(stepid)
    self.setName( '3. Quantify and show the differences' )
    self.setDescription( 'Find small differences between the baseline and follow-up volumes.' )
    
    self.__parent = super(QuantificationStep, self)

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
    pass