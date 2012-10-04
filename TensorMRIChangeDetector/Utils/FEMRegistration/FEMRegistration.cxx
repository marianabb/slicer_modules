#include "itkImage.h"
#include "itkImageFileReader.h"
#include "itkImageFileWriter.h"

#include "itkRescaleIntensityImageFilter.h"
#include "itkHistogramMatchingImageFilter.h"
#include "itkFEMRegistrationFilter.h"

#include "FEMRegistrationCLP.h"

typedef char PixelType;
typedef float OutPixelType;
const unsigned int Dimension = 3;
typedef itk::fem::FEMObject<Dimension> FEMObjectType;
typedef itk::Image<OutPixelType, Dimension> ImageType; // ALL FLOATS
typedef itk::Image<OutPixelType, Dimension> OutImageType;
typedef itk::fem::Element3DC0LinearHexahedronMembrane ElementType;

typedef itk::ImageFileReader< ImageType > ReaderType;
typedef itk::ImageFileWriter< ImageType > WriterType;
typedef itk::ImageFileWriter< OutImageType > OutWriterType;
typedef itk::fem::FEMRegistrationFilter<OutImageType,OutImageType,FEMObjectType> RegistrationType;


int main(int argc, char ** argv) {

  PARSE_ARGS;

  // Create readers for the inputs
  ReaderType::Pointer reader_fixedV = ReaderType::New(); // Fixed Volume
  ReaderType::Pointer reader_movingV = ReaderType::New(); // Moving Volume

  // Obtain values from the CLI
  const char *inputFixed = fixedVolume.c_str();
  const char *inputMoving = movingVolume.c_str();

  // Fill in the readers
  reader_fixedV->SetFileName(inputFixed);
  reader_movingV->SetFileName(inputMoving);
  reader_fixedV->Update();
  reader_movingV->Update();


  RegistrationType::Pointer registrationFilter = RegistrationType::New();
  registrationFilter->SetMaxLevel(1);
  registrationFilter->SetUseNormalizedGradient( true );
  // 0 = mean squares, 1 = cross correlation, 2 = pattern intensity, 3 = mutual information.
  registrationFilter->ChooseMetric(3);

  unsigned int maxiters = 20;
  float        E = 100;
  float        p = 1;
  registrationFilter->SetElasticity(E, 0);
  registrationFilter->SetRho(p, 0);
  registrationFilter->SetGamma(1., 0);
  registrationFilter->SetAlpha(1.);
  registrationFilter->SetMaximumIterations( maxiters, 0 );
  registrationFilter->SetMeshPixelsPerElementAtEachResolution(14, 0);
  registrationFilter->SetWidthOfMetricRegion(1, 0);
  registrationFilter->SetNumberOfIntegrationPoints(2, 0);
  registrationFilter->SetDoLineSearchOnImageEnergy( 0 );
  registrationFilter->SetTimeStep(1.);
  registrationFilter->SetEmployRegridding(false);
  registrationFilter->SetUseLandmarks(false);


  // Rescale the image intensities so that they fall between 0 and 255
  typedef itk::RescaleIntensityImageFilter<ImageType,OutImageType> FilterType;
  FilterType::Pointer movingrescalefilter = FilterType::New();
  FilterType::Pointer fixedrescalefilter = FilterType::New();

  movingrescalefilter->SetInput(reader_movingV->GetOutput());
  fixedrescalefilter->SetInput(reader_fixedV->GetOutput());

  const double desiredMinimum =  0.0;
  const double desiredMaximum =  255.0;

  movingrescalefilter->SetOutputMinimum( desiredMinimum );
  movingrescalefilter->SetOutputMaximum( desiredMaximum );
  movingrescalefilter->UpdateLargestPossibleRegion();
  fixedrescalefilter->SetOutputMinimum( desiredMinimum );
  fixedrescalefilter->SetOutputMaximum( desiredMaximum );
  fixedrescalefilter->UpdateLargestPossibleRegion();


  // Histogram match the images
  typedef itk::HistogramMatchingImageFilter<OutImageType,OutImageType> HEFilterType;
  HEFilterType::Pointer IntensityEqualizeFilter = HEFilterType::New();

  IntensityEqualizeFilter->SetReferenceImage( fixedrescalefilter->GetOutput() );
  IntensityEqualizeFilter->SetInput( movingrescalefilter->GetOutput() );
  IntensityEqualizeFilter->SetNumberOfHistogramLevels(50); //100
  IntensityEqualizeFilter->SetNumberOfMatchPoints( 15);
  IntensityEqualizeFilter->ThresholdAtMeanIntensityOn();
  IntensityEqualizeFilter->Update();

  // Set the images for registration filter
  registrationFilter->SetFixedImage(fixedrescalefilter->GetOutput());
  registrationFilter->SetMovingImage(IntensityEqualizeFilter->GetOutput());


//   itk::ImageFileWriter<ImageType>::Pointer writer;
//   writer = itk::ImageFileWriter<ImageType>::New();
//   std::string ofn="fixed.mha";
//   writer->SetFileName(ofn.c_str());
//   writer->SetInput(registrationFilter->GetFixedImage() );

//   try
//   {
//     writer->Write();
//   }
//   catch( itk::ExceptionObject & excp )
//   {
//     std::cerr << excp << std::endl;
//     return EXIT_FAILURE;
//   }

//   ofn="moving.mha";
//   itk::ImageFileWriter<ImageType>::Pointer writer2;
//   writer2 =  itk::ImageFileWriter<ImageType>::New();
//   writer2->SetFileName(ofn.c_str());
//   writer2->SetInput(registrationFilter->GetMovingImage() );

//   try
//   {
//     writer2->Write();
//   }
//   catch( itk::ExceptionObject & excp )
//   {
//     std::cerr << excp << std::endl;
//     return EXIT_FAILURE;
//   }


//  In order to initialize the mesh of elements, we must first create
//  ``dummy'' material and element objects and assign them to the
//  registration filter.  These objects are subsequently used to
//  either read a predefined mesh from a file or generate a mesh using
//  the software.  The values assigned to the fields within the
//  material object are arbitrary since they will be replaced with
//  those specified earlier.  Similarly, the element
//  object will be replaced with those from the desired mesh.
//

  // Create the material properties
  itk::fem::MaterialLinearElasticity::Pointer m;
  m = itk::fem::MaterialLinearElasticity::New();
  m->SetGlobalNumber(0);
  m->SetYoungsModulus(registrationFilter->GetElasticity()); // Young's modulus of the membrane
  m->SetCrossSectionalArea(1.0);                            // Cross-sectional area
  m->SetThickness(1.0);                                     // Thickness
  m->SetMomentOfInertia(1.0);                               // Moment of inertia
  m->SetPoissonsRatio(0.);                                  // Poisson's ratio -- DONT CHOOSE 1.0!!
  m->SetDensityHeatProduct(1.0);                            // Density-Heat capacity product

  // Create the element type
  ElementType::Pointer e1=ElementType::New();
  e1->SetMaterial(m.GetPointer());
  registrationFilter->SetElement(e1.GetPointer());
  registrationFilter->SetMaterial(m);

  // Now we are ready to run the registration:
  registrationFilter->RunRegistration();


//  To output the image resulting from the registration, we can call
//  \code{GetWarpedImage()}.  The image is written in floating point
//  format.

//   itk::ImageFileWriter<ImageType>::Pointer warpedImageWriter;
//   warpedImageWriter = itk::ImageFileWriter<ImageType>::New();
//   warpedImageWriter->SetInput( registrationFilter->GetWarpedImage() );
//   warpedImageWriter->SetFileName("warpedMovingImage.mha");
//   try
//   {
//     warpedImageWriter->Update();
//   }
//   catch( itk::ExceptionObject & excp )
//   {
//     std::cerr << excp << std::endl;
//     return EXIT_FAILURE;
//   }


//  We can also output the displacement field resulting from the
//  registration; we can call \code{GetDisplacementField()} to get the
//  multi-component image.

  typedef itk::ImageFileWriter<RegistrationType::FieldType> DispWriterType;
  DispWriterType::Pointer dispWriter = DispWriterType::New();
  dispWriter->SetInput( registrationFilter->GetDisplacementField() );
  //dispWriter->SetFileName("displacement.mha");
  dispWriter->SetFileName(deformationField.c_str());
  try
  {
    dispWriter->Update();
  }
  catch( itk::ExceptionObject & excp )
  {
    std::cerr << excp << std::endl;
    return EXIT_FAILURE;
  }

  return EXIT_SUCCESS;
}
