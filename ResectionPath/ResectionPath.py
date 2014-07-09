import os
import unittest
from __main__ import vtk, qt, ctk, slicer

#
# ResectionPath
#

class ResectionPath:
  def __init__(self, parent):
    parent.title = "ResectionPath" # TODO make this more human readable by adding spaces
    parent.categories = ["IGT"]
    parent.dependencies = []
    parent.contributors = ["Matt Lougheed (Queen's University)"] # replace with "Firstname Lastname (Organization)"
    parent.helpText = """
    This module uses fiducial points to create a 3D shape representing a resection
    """
    parent.acknowledgementText = """

""" # replace with organization, grant and thanks.
    self.parent = parent

    # Add this test to the SelfTest module's list for discovery when the module
    # is created.  Since this module may be discovered before SelfTests itself,
    # create the list if it doesn't already exist.
    try:
      slicer.selfTests
    except AttributeError:
      slicer.selfTests = {}
    slicer.selfTests['ResectionPath'] = self.runTest

  def runTest(self):
    tester = ResectionPathTest()
    tester.runTest()

#
# ResectionPathWidget
#

class ResectionPathWidget:
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

    #
    # Reload and Test area
    #
    reloadCollapsibleButton = ctk.ctkCollapsibleButton()
    reloadCollapsibleButton.text = "Reload && Test"
    self.layout.addWidget(reloadCollapsibleButton)
    reloadFormLayout = qt.QFormLayout(reloadCollapsibleButton)

    # reload button
    # (use this during development, but remove it when delivering
    #  your module to users)
    self.reloadButton = qt.QPushButton("Reload")
    self.reloadButton.toolTip = "Reload this module."
    self.reloadButton.name = "ResectionPath Reload"
    reloadFormLayout.addWidget(self.reloadButton)
    self.reloadButton.connect('clicked()', self.onReload)

    # reload and test button
    # (use this during development, but remove it when delivering
    #  your module to users)
    self.reloadAndTestButton = qt.QPushButton("Reload and Test")
    self.reloadAndTestButton.toolTip = "Reload this module and then run the self tests."
    reloadFormLayout.addWidget(self.reloadAndTestButton)
    self.reloadAndTestButton.connect('clicked()', self.onReloadAndTest)

    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    #
    # Fiducial Selector
    #
    self.fiducialSelector = slicer.qMRMLNodeComboBox()
    self.fiducialSelector.nodeTypes = (("vtkMRMLMarkupsFiducialNode"), "")
    self.fiducialSelector.addEnabled = False
    self.fiducialSelector.removeEnabled = False
    self.fiducialSelector.noneEnabled = True
    self.fiducialSelector.showHidden = False
    self.fiducialSelector.renameEnabled = True
    self.fiducialSelector.showChildNodeTypes = False
    self.fiducialSelector.setMRMLScene(slicer.mrmlScene)
    self.fiducialSelector.setToolTip("Select the fiducials to use for the resection area")
    parametersFormLayout.addRow("Fiducial points: ", self.fiducialSelector)

    #
    # Model Selector
    #
    self.modelSelector = slicer.qMRMLNodeComboBox()
    self.modelSelector.nodeTypes = (("vtkMRMLModelNode"), "")
    self.modelSelector.addEnabled = True
    self.modelSelector.removeEnabled = False
    self.modelSelector.noneEnabled = True
    self.modelSelector.showHidden = False
    self.modelSelector.renameEnabled = True
    self.modelSelector.selectNodeUponCreation = True
    self.modelSelector.showChildNodeTypes = False
    self.modelSelector.setMRMLScene(slicer.mrmlScene)
    self.modelSelector.setToolTip("Choose the model node.")
    parametersFormLayout.addRow("Resection area model: ", self.modelSelector)

    #
    # Generate Button
    #
    self.generateButton = qt.QPushButton("Generate")
    self.generateButton.toolTip = "Generate the resection area"
    self.generateButton.enabled = False
    parametersFormLayout.addRow(self.generateButton)

    #
    # Connections
    #
    self.generateButton.connect('clicked(bool)', self.onGenerateButton)
    self.fiducialSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.modelSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)

    # Add vertical spacer
    self.layout.addStretch(1)

  def cleanup(self):
    pass

  def onSelect(self):
    if (self.fiducialSelector.currentNode() != None and self.modelSelector.currentNode() != None):
      self.generateButton.setDisabled(False)
    else:
      self.generateButton.setDisabled(True)

  def onGenerateButton(self):
    if (self.fiducialSelector.currentNode() != None and self.modelSelector.currentNode() != None):
      if (self.fiducialSelector.currentNode().GetNumberOfFiducials() > 3):
        logic = ResectionPathLogic()
        logic.generateResectionVolume(self.fiducialSelector.currentNode(), self.modelSelector.currentNode())
      else:
        qt.QMessageBox.warning(slicer.util.mainWindow(), "Generate Button", 'Error: You need at least 4 points to generate the resection area object')


  def onReload(self,moduleName="ResectionPath"):
    """Generic reload method for any scripted module.
    ModuleWizard will subsitute correct default moduleName.
    """
    globals()[moduleName] = slicer.util.reloadScriptedModule(moduleName)

  def onReloadAndTest(self,moduleName="ResectionPath"):
    try:
      self.onReload()
      evalString = 'globals()["%s"].%sTest()' % (moduleName, moduleName)
      tester = eval(evalString)
      tester.runTest()
    except Exception, e:
      import traceback
      traceback.print_exc()
      qt.QMessageBox.warning(slicer.util.mainWindow(),
          "Reload and Test", 'Exception!\n\n' + str(e) + "\n\nSee Python Console for Stack Trace")


#
# ResectionPathLogic
#

class ResectionPathLogic:
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget
  """
  def __init__(self):
    pass

  def updatePoints(self):
    points = vtk.vtkPoints()
    cellArray = vtk.vtkCellArray()

    numberOfPoints = self.FiducialNode.GetNumberOfFiducials()
    points.SetNumberOfPoints(numberOfPoints)
    x = [0.0, 0.0, 0.0]
    for i in range(numberOfPoints):
      self.FiducialNode.GetNthFiducialPosition(i,x)
      points.SetPoint(i, x)

    self.PolyData.SetPoints(points)

  def updateResectionVolume(self, caller, event):
    if (caller.IsA('vtkMRMLMarkupsFiducialNode') and event == 'ModifiedEvent'):
        self.updatePoints()

  def generateResectionVolume(self, fiducialNode, modelNode):
    if (fiducialNode != None):
      self.FiducialNode = fiducialNode
      self.PolyData = vtk.vtkPolyData()
      self.updatePoints()

      self.Delaunay = vtk.vtkDelaunay3D()
      self.Delaunay.SetInputData(self.PolyData)
      self.Delaunay.Update()

      self.SurfaceFilter = vtk.vtkDataSetSurfaceFilter()
      self.SurfaceFilter.SetInputConnection(self.Delaunay.GetOutputPort())
      self.SurfaceFilter.Update()

      if modelNode.GetDisplayNodeID() == None:
        modelDisplayNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLModelDisplayNode")
        modelDisplayNode.SetColor(0,0,1) # Blue
        #modelDisplayNode.BackfaceCullingOff()
        modelDisplayNode.SetOpacity(0.3) # Between 0-1, 1 being opaque
        slicer.mrmlScene.AddNode(modelDisplayNode)
        modelNode.SetAndObserveDisplayNodeID(modelDisplayNode.GetID())

      modelNode.SetPolyDataConnection(self.SurfaceFilter.GetOutputPort())
      modelNode.Modified()
      slicer.mrmlScene.AddNode(modelNode)

      self.tag = self.FiducialNode.AddObserver('ModifiedEvent', self.updateResectionVolume)


class ResectionPathTest(unittest.TestCase):
  """
  This is the test case for your scripted module.
  """

  def delayDisplay(self,message,msec=1000):
    """This utility method displays a small dialog and waits.
    This does two things: 1) it lets the event loop catch up
    to the state of the test so that rendering and widget updates
    have all taken place before the test continues and 2) it
    shows the user/developer/tester the state of the test
    so that we'll know when it breaks.
    """
    print(message)
    self.info = qt.QDialog()
    self.infoLayout = qt.QVBoxLayout()
    self.info.setLayout(self.infoLayout)
    self.label = qt.QLabel(message,self.info)
    self.infoLayout.addWidget(self.label)
    qt.QTimer.singleShot(msec, self.info.close)
    self.info.exec_()

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_ResectionPath1()

  def test_ResectionPath1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests sould exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")
    #
    # first, get some data
    #
    import urllib
    downloads = (
        ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
        )

    for url,name,loader in downloads:
      filePath = slicer.app.temporaryPath + '/' + name
      if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        print('Requesting download %s from %s...\n' % (name, url))
        urllib.urlretrieve(url, filePath)
      if loader:
        print('Loading %s...\n' % (name,))
        loader(filePath)
    self.delayDisplay('Finished with download and loading\n')

    volumeNode = slicer.util.getNode(pattern="FA")
    logic = ResectionPathLogic()
    self.assertTrue( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
