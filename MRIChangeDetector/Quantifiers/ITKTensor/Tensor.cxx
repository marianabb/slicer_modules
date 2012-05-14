#include "itkImage.h"
#include "itkImageFileReader.h"
#include "itkImageFileWriter.h"
#include "itkImageDuplicator.h"
#include "itkImageRegionIteratorWithIndex.h"
#include "itkDisplacementFieldJacobianDeterminantFilter.h"

#include "TensorCLP.h"

typedef int PixelType;
typedef float JacPixelType;
const unsigned int Dimension = 3;

typedef itk::Image< PixelType, Dimension > ImageType; // We assume the input and output images have the same type
typedef itk::Image< JacPixelType, Dimension > JacImageType; // Jacobian image type
typedef itk::Image<itk::Vector<JacPixelType, Dimension>, Dimension> DFImageType; // Deformation field image type

typedef itk::ImageFileReader< ImageType > ReaderType;
typedef itk::ImageFileReader< DFImageType > DFReaderType;
typedef itk::ImageFileWriter< ImageType > WriterType;
typedef itk::ImageDuplicator<ImageType> DuplicatorType;

typedef itk::ImageRegionIteratorWithIndex<ImageType> IteratorType;
typedef itk::DisplacementFieldJacobianDeterminantFilter<DFImageType, JacPixelType, JacImageType> JacFilterType; // Jacobian filter


int main( int argc, char ** argv ) {
  
  PARSE_ARGS;
  
  // Create readers for the inputs
  ReaderType::Pointer reader_fixedV = ReaderType::New(); // Fixed Volume
  DFReaderType::Pointer reader_demonsDF = DFReaderType::New(); // Deformation field resulting from BRAINSDemonWarp
  
  // Obtain values from the CLI
  const char * inputFixed = fixedVolume.c_str();
  const char * inputDF = deformationField.c_str();

  reader_fixedV->SetFileName(inputFixed);
  reader_demonsDF->SetFileName(inputDF);
  
  // Fill in the readers
  reader_fixedV->Update();
  reader_demonsDF->Update();

  // Create the jacobian filter and fill in the parameter
  JacFilterType::Pointer jacFilter = JacFilterType::New();
  jacFilter->SetInput(reader_demonsDF->GetOutput());
  jacFilter->SetUseImageSpacingOn();
  jacFilter->Update();

  // Apply the filter and obtain the result image
  JacImageType::Pointer jacImage = jacFilter->GetOutput();

  ImageType::Pointer fixedImage = reader_fixedV->GetOutput(), changesLabel;

  DuplicatorType::Pointer dup = DuplicatorType::New();
  dup->SetInputImage(reader_fixedV->GetOutput());
  dup->Update();
  changesLabel = dup->GetOutput();
  changesLabel->FillBuffer(0);
  
  
 
  // Iterate over the image and label according to the jacobian
  float jacDetSum = 0, nSegVoxels = 0;
  IteratorType bIt(fixedImage, fixedImage->GetBufferedRegion());

  //float growthPixels = 0, shrinkPixels = 0;
  for(bIt.GoToBegin(); !bIt.IsAtEnd(); ++bIt){
    ImageType::IndexType idx = bIt.GetIndex();
    ImageType::PixelType bPxl = bIt.Get();
    
    if(bPxl){
      JacImageType::PixelType jPxl = jacImage->GetPixel(idx);
      jacDetSum += jPxl;
      nSegVoxels++;
      if(jPxl > 1.1)
        changesLabel->SetPixel(idx, 14); // Local Expansion, Pink in labelMap
      if(jPxl < 0.9)
        changesLabel->SetPixel(idx, 12); // Local Shrinking, Green in labelMap
    }
  }

  // Create a writer for the output
  WriterType::Pointer writer = WriterType::New();
  writer->SetInput(changesLabel);
  writer->SetFileName(outputVolume.c_str());  
  writer->Update();


  ImageType::SpacingType s = changesLabel->GetSpacing();
  float sv = s[0]*s[1]*s[2];
  std::cout << "sv = " << sv << std::endl;
  std::cout << "jacDetSum = " << jacDetSum << std::endl;
  std::cout << "nSegVoxels = " << nSegVoxels << std::endl;
  std::cout << "Growth: " << (jacDetSum-nSegVoxels)*sv << " mm^3 (" << jacDetSum-nSegVoxels << " pixels) " << std::endl;
  //  std::cout << "Shrinkage: " << shrinkPixels*sv << " mm^3 (" << shrinkPixels << " pixels) " << std::endl;
  // std::cout << "Total: " << (growthPixels-shrinkPixels)*sv << " mm^3 (" << growthPixels-shrinkPixels << " pixels) " << std::endl

  return EXIT_SUCCESS;

}
