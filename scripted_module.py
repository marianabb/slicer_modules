
### First example
# To load a volume
slicer.util.loadVolume("/home/mariana/thesis/volumes/first_batch/patient1-us1/test.dcm")
# Once loaded, obtain the Node
n = getNode('test')

# To run a CLI from Python, in this case 'grayscalemodelmaker'
# More modules in slicer.modules
def grayModel(volumeNode):
    parameters = {}
    parameters["InputVolume"] = volumeNode.GetID()
    outModel = slicer.vtkMRMLModelNode()
    slicer.mrmlScene.AddNode( outModel )
    parameters["OutputGeometry"] = outModel.GetID()

    parameters["Threshold"] = 70
    
    grayMaker = slicer.modules.grayscalemodelmaker
    slicer.cli.run(grayMaker, None, parameters)


# Volume from the sample data that works with our CLI
v = getNode('MRHead')
grayModel(v)



### Numpy, VTK, matplotlib example
import vtk
import slicer
mrml = slicer.vtkMRMLScene()
vl = slicer.vtkSlicerVolumesLogic()
vl.SetAndObserveMRMLScene(mrml)
n = vl.AddArchetypeVolume('../../Testing/Data/Input/MRHeadResampled.nhdr', 'CTC')
i = n.GetImageData()
print (i.GetScalarRange())

import vtk.util.numpy_support
a = vtk.util.numpy_support.vtk_to_numpy(i.GetPointData().GetScalars())
print(a.min(),a.max())

# Matplotlib doesn't come with Slicer, must be installed separately
import matplotlib
import matplotlib.pyplot
n, bins, patches = matplotlib.pyplot.hist(a, 50, facecolor='g', alpha=0.75)
matplotlib.pyplot.show()


### What is accesible via Python

### 1. Qt
import slicer

def widgetTree(root=""):
  if not root:
    root = slicer.util.mainWindow()
  global treeItems
  tree = qt.QTreeWidget()
  tree.setHeaderLabels(["Widget", "Class", "Title", "Text", "Name"])
  treeItems = {}
  treeItems[root] = qt.QTreeWidgetItem(tree)
  parents = [root]
  while parents != []:
    widget = parents.pop()
    if not widget:
      break
    widgetItem = qt.QTreeWidgetItem(treeItems[widget])
    children = widget.children()
    for child in children:
      treeItems[child] = widgetItem
    parents += children
    widgetItem.setText(0, str(widget))
    try:
      widgetItem.setText(1, widget.className())
    except AttributeError:
      pass
    try:
      widgetItem.setText(2, widget.title)
    except AttributeError:
      pass
    try:
      widgetItem.setText(3, widget.text)
    except AttributeError:
      pass
    try:
      widgetItem.setText(4, widget.name)
    except AttributeError:
      pass
  tree.setGeometry(100, 100, 1000, 500)
  tree.setColumnWidth(0,200)
  tree.setColumnWidth(0,300)
  tree.expandAll()
  tree.show()
  return tree


### 2. VTK and MRML
class EndoscopyPathModel:
  """Create a vtkPolyData for a polyline:
       - Add one point per path point.
       - Add a single polyline
  """
  def __init__(self, path, fiducialListNode):
  
    fids = fiducialListNode
    scene = slicer.mrmlScene
    
    points = vtk.vtkPoints()
    polyData = vtk.vtkPolyData()
    polyData.SetPoints(points)

    lines = vtk.vtkCellArray()
    polyData.SetLines(lines)
    linesIDArray = lines.GetData()
    linesIDArray.Reset()
    linesIDArray.InsertNextTuple1(0)

    polygons = vtk.vtkCellArray()
    polyData.SetPolys( polygons )
    idArray = polygons.GetData()
    idArray.Reset()
    idArray.InsertNextTuple1(0)

    for point in path:
      pointIndex = points.InsertNextPoint(*point)
      linesIDArray.InsertNextTuple1(pointIndex)
      linesIDArray.SetTuple1( 0, linesIDArray.GetNumberOfTuples() - 1 )
      lines.SetNumberOfCells(1)
      
    # Create model node
    model = slicer.vtkMRMLModelNode()
    model.SetScene(scene)
    model.SetName("Path-%s" % fids.GetName())
    model.SetAndObservePolyData(polyData)

    # Create display node
    modelDisplay = slicer.vtkMRMLModelDisplayNode()
    modelDisplay.SetColor(1,1,0) # yellow
    modelDisplay.SetScene(scene)
    scene.AddNodeNoNotify(modelDisplay)
    model.SetAndObserveDisplayNodeID(modelDisplay.GetID())

    # Add to scene
    modelDisplay.SetPolyData(model.GetPolyData())
    scene.AddNode(model)

    # Camera cursor
    sphere = vtk.vtkSphereSource()
    sphere.Update()
     
    # Create model node
    cursor = slicer.vtkMRMLModelNode()
    cursor.SetScene(scene)
    cursor.SetName("Cursor-%s" % fids.GetName())
    cursor.SetAndObservePolyData(sphere.GetOutput())

    # Create display node
    cursorModelDisplay = slicer.vtkMRMLModelDisplayNode()
    cursorModelDisplay.SetColor(1,0,0) # red
    cursorModelDisplay.SetScene(scene)
    scene.AddNodeNoNotify(cursorModelDisplay)
    cursor.SetAndObserveDisplayNodeID(cursorModelDisplay.GetID())

    # Add to scene
    cursorModelDisplay.SetPolyData(sphere.GetOutput())
    scene.AddNode(cursor)

    # Create transform node
    transform = slicer.vtkMRMLLinearTransformNode()
    transform.SetName('Transform-%s' % fids.GetName())
    scene.AddNode(transform)
    cursor.SetAndObserveTransformNodeID(transform.GetID())
    
    self.transform = transform



### 3. Numpy
#
# Get the numpy array for the bg and label
#
import vtk.util.numpy_support
backgroundImage = backgroundNode.GetImageData()
labelImage = labelNode.GetImageData()
shape = list(backgroundImage.GetDimensions())
shape.reverse()
backgroundArray = vtk.util.numpy_support.vtk_to_numpy(backgroundImage.GetPointData().GetScalars()).reshape(shape)
labelArray = vtk.util.numpy_support.vtk_to_numpy(labelImage.GetPointData().GetScalars()).reshape(shape)


### 4. CLI Modules
def onApply(self):
    #
    # create a model using the command line module
    # based on the current editor parameters
    #

    volumeNode = self.editUtil.getLabelVolume()
    if not volumeNode:
      return

    #
    # set up the model maker node
    #

    parameters = {}
    parameters['Name'] = self.modelName.text
    parameters["InputVolume"] = volumeNode.GetID()
    parameters['FilterType'] = "Sinc"

    # build only the currently selected model.
    parameters['Labels'] = self.getPaintLabel()
    parameters["StartLabel"] = -1
    parameters["EndLabel"] = -1
    
    parameters['GenerateAll'] = False
    parameters["JointSmoothing"] = False
    parameters["SplitNormals"] = True
    parameters["PointNormals"] = True
    parameters["SkipUnNamed"] = True

    if self.smooth.checked:
      parameters["Decimate"] = 0.25
      parameters["Smooth"] = 10
    else:
      parameters["Decimate"] = 0
      parameters["Smooth"] = 0

    #
    # output 
    # - make a new hierarchy node if needed
    #
    numNodes = slicer.mrmlScene.GetNumberOfNodesByClass( "vtkMRMLModelHierarchyNode" )
    outHierarchy = None
    for n in xrange(numNodes):
      node = slicer.mrmlScene.GetNthNodeByClass( n, "vtkMRMLModelHierarchyNode" )
      if node.GetName() == "Editor Models":
        outHierarchy = node
        break

    if not outHierarchy:
      outHierarchy = slicer.vtkMRMLModelHierarchyNode()
      outHierarchy.SetScene( slicer.mrmlScene )
      outHierarchy.SetName( "Editor Models" )
      slicer.mrmlScene.AddNode( outHierarchy )

    parameters["ModelSceneFile"] = outHierarchy

    modelMaker = slicer.modules.modelmaker

    # 
    # run the task (in the background)
    # - use the GUI to provide progress feedback
    # - use the GUI's Logic to invoke the task
    # - model will show up when the processing is finished
    #
    self.CLINode = slicer.cli.run(modelMaker, self.CLINode, parameters)

    self.statusText( "Model Making Started..." )