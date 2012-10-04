#include "itkImage.h"
#include "itkImageFileReader.h"
#include "itkImageFileWriter.h"
#include "itkImageDuplicator.h"
#include "itkImageRegionIteratorWithIndex.h"
#include "itkDisplacementFieldJacobianDeterminantFilter.h"
#include "itkCastImageFilter.h"
#include "itkRescaleIntensityImageFilter.h"
#include "itkMinimumMaximumImageCalculator.h"
#include "itkLogImageFilter.h"

#include "TensorCLP.h"

typedef char PixelType;
typedef float OutPixelType;
typedef float JacPixelType;
const unsigned int Dimension = 3;

typedef itk::Image< PixelType, Dimension > ImageType;
typedef itk::Image< OutPixelType, Dimension > OutImageType;
typedef itk::Image< JacPixelType, Dimension > JacImageType; // Jacobian image type
typedef itk::Image<itk::Vector<JacPixelType, Dimension>, Dimension> DFImageType; // Deformation field image type

typedef itk::ImageFileReader< ImageType > ReaderType;
typedef itk::ImageFileReader< DFImageType > DFReaderType;
typedef itk::ImageFileWriter< ImageType > WriterType;
typedef itk::ImageFileWriter< OutImageType > OutWriterType;
typedef itk::ImageDuplicator<ImageType> DuplicatorType;

typedef itk::ImageRegionIteratorWithIndex<ImageType> IteratorType;
typedef itk::DisplacementFieldJacobianDeterminantFilter<DFImageType, JacPixelType, JacImageType> JacFilterType; // Jacobian filter

typedef itk::CastImageFilter< ImageType, OutImageType > CastFilterType; // Filter to cast from ImageType to OutImageType
typedef itk::MinimumMaximumImageCalculator <JacImageType> ImageCalculatorFilterType;
typedef itk::LogImageFilter< OutImageType, OutImageType > LogFilterType;
typedef itk::RescaleIntensityImageFilter< OutImageType, OutImageType > RescaleFilterType;


//JacImageType::PixelType GetMaximumJacobian(JacImageType::Pointer image);

int main(int argc, char ** argv) {
  
  PARSE_ARGS;

  // Create readers for the inputs
  ReaderType::Pointer reader_fixedV = ReaderType::New(); // Fixed Volume
  DFReaderType::Pointer reader_demonsDF = DFReaderType::New(); // Deformation field resulting from BRAINSDemonWarp
  
  // Obtain values from the CLI
  const char * inputFixed = fixedVolume.c_str();
  const char * inputDF = deformationField.c_str();

  // Fill in the readers
  reader_fixedV->SetFileName(inputFixed);
  reader_demonsDF->SetFileName(inputDF);
  reader_fixedV->Update();
  reader_demonsDF->Update();

  // Create the jacobian filter and fill in the parameter
  JacFilterType::Pointer jacFilter = JacFilterType::New();
  jacFilter->SetInput(reader_demonsDF->GetOutput());
  jacFilter->SetUseImageSpacingOn();
  jacFilter->Update();

  // Apply the filter and obtain the result image
  JacImageType::Pointer jacImage = jacFilter->GetOutput();

  //--- Maximum and minumum Jacobians
  ImageCalculatorFilterType::Pointer imageCalculatorFilter = ImageCalculatorFilterType::New();
  imageCalculatorFilter->SetImage(jacImage);
  imageCalculatorFilter->ComputeMaximum();
  imageCalculatorFilter->ComputeMinimum();
  
  JacImageType::PixelType maxJacobian = log(imageCalculatorFilter->GetMaximum()); //Added log
  JacImageType::PixelType minJacobian = log(imageCalculatorFilter->GetMinimum()); //Added log
  std::cout << "log(Max Jacobian) = " << maxJacobian << std::endl;
  std::cout << "log(min Jacobian) = " << minJacobian << std::endl;
  // ---

  // Create the fixed image using the reader
  ImageType::Pointer fixedImage = reader_fixedV->GetOutput(), changesLabel;

  // Duplicate the fixed image to create the label map
  DuplicatorType::Pointer dup = DuplicatorType::New();
  dup->SetInputImage(reader_fixedV->GetOutput());
  dup->Update();
  changesLabel = dup->GetOutput();
  changesLabel->FillBuffer(0);

  // Create a new image with the same size for the output. But with floats instead of ints.
  OutImageType::Pointer OutImage = OutImageType::New();
  OutImageType::IndexType start;
  start[0] = 0;
  start[1] = 0;
  start[2] = 0;
  // Both the size and the spacing must be the same as the fixedImage
  OutImageType::SizeType size = fixedImage->GetLargestPossibleRegion().GetSize();
  OutImageType::SpacingType spacing = fixedImage->GetSpacing();
  OutImageType::RegionType region;
  region.SetSize(size);
  region.SetIndex(start);
  OutImage->SetSpacing(spacing);
  OutImage->SetRegions(region);
  OutImage->Allocate();

  // Calculate the range and the percentages we want to take
  JacImageType::PixelType h_bound = abs(maxJacobian - minJacobian) * 0.44;//0.3642; //0.225;
  JacImageType::PixelType l_bound = abs(maxJacobian - minJacobian) * 0.4453;
  JacImageType::PixelType higher_bound = maxJacobian - h_bound;
  JacImageType::PixelType lower_bound = minJacobian + l_bound;

  // Iterate over the image and label according to the jacobian
  float jacDetSum = 0, nSegVoxels = 0;
  IteratorType bIt(fixedImage, fixedImage->GetBufferedRegion());

  //float growthPixels = 0, shrinkPixels = 0;
  for(bIt.GoToBegin(); !bIt.IsAtEnd(); ++bIt){
    ImageType::IndexType idx = bIt.GetIndex();
    ImageType::PixelType bPxl = bIt.Get();
    
    if(bPxl){
      JacImageType::PixelType jPxl = log(jacImage->GetPixel(idx)); //Added log
      jacDetSum += jPxl; //TODO Do something with this
      nSegVoxels++;
      
      if((jPxl > 0.1) && (jPxl >= higher_bound))
        changesLabel->SetPixel(idx, 14); // Local Expansion, avery(pink) in labelMap
      if((jPxl > -0.1) && (jPxl <= 0.1))
        changesLabel->SetPixel(idx, 0); // No change, or almost no change, Black in labelMap
      if((jPxl < -0.1) && (jPxl <= lower_bound))
        changesLabel->SetPixel(idx, 12); // Local Shrinking, elwood(green) in labelMap

      // Fill the output image with the jacobian values. 
      // Apply logarithm to make the differences more noticeable.
      if(jPxl < 0.0){
        //OutImage->SetPixel(idx, (log(1 + abs(jPxl)) * (-1)));
        OutImage->SetPixel(idx, jPxl);
      } else {
        //OutImage->SetPixel(idx, log(1 + jPxl));
        OutImage->SetPixel(idx, jPxl);
      }
    }
  }
  
  // Rescale the output volume intensities between 0 and 255
  RescaleFilterType::Pointer rescaleFilter = RescaleFilterType::New();
  rescaleFilter->SetInput(OutImage);  
  rescaleFilter->SetOutputMinimum(0);
  rescaleFilter->SetOutputMaximum(255);
  

  // Create a writer for the output label
  WriterType::Pointer labelWriter = WriterType::New();
  labelWriter->SetInput(changesLabel);
  labelWriter->SetFileName(outputLabelMap.c_str());  
  labelWriter->Update();


  // Create a writer for the output volume
  OutWriterType::Pointer OutWriter = OutWriterType::New();
  OutWriter->SetInput(OutImage); 
  //OutWriter->SetInput(rescaleFilter->GetOutput());
  OutWriter->SetFileName(outputVolume.c_str());  
  OutWriter->Update();


  ImageType::SpacingType s = changesLabel->GetSpacing();
  float sv = s[0]*s[1]*s[2]; // 1
  std::cout << "jacDetSum = " << jacDetSum << std::endl;
  std::cout << "nSegVoxels = " << nSegVoxels << std::endl;
  std::cout << "Growth: " << (jacDetSum-nSegVoxels)*sv << " mm^3 (" << jacDetSum-nSegVoxels << " pixels) " << std::endl;
  //  std::cout << "Shrinkage: " << shrinkPixels*sv << " mm^3 (" << shrinkPixels << " pixels) " << std::endl;
  // std::cout << "Total: " << (growthPixels-shrinkPixels)*sv << " mm^3 (" << growthPixels-shrinkPixels << " pixels) " << std::endl
 
  return EXIT_SUCCESS;
}
