# DataCore Analytics - Testing Guide

## Quick Start Testing

### 1. Start the Server
```bash
cd /workspace/data-analyzer-project
./START_SERVER.sh
```

Or manually:
```bash
cd /workspace/data-analyzer-project
python3 manage.py runserver 0.0.0.0:8000
```

### 2. Access the Application
Open browser and navigate to: `http://localhost:8000/`

### 3. Test File Upload

Use the test file provided at: `/workspace/test_employee_data.csv`

Or create your own CSV with columns like:
```csv
Name,Age,Salary,Department,Experience
John Doe,28,50000,Sales,3
Jane Smith,32,65000,Marketing,5
...
```

## Complete Test Checklist

### Upload Functionality
- [ ] Navigate to homepage
- [ ] Drag and drop file to upload area
- [ ] Click to browse and select file
- [ ] Select file type (CSV or Excel)
- [ ] Observe file validation feedback
- [ ] Enter optional email address
- [ ] Click "Analyze Data" button
- [ ] Observe loading spinner
- [ ] Verify results page loads

### Results Page Layout
- [ ] Check header size is reasonable (not oversized)
- [ ] Verify stats overview cards display correctly
- [ ] Scroll through page - no content hidden behind header
- [ ] Expand "Initial Data Summary" section
- [ ] Expand "Final Data Summary" section
- [ ] Verify all visualizations display properly
- [ ] Check responsive design on smaller screen sizes

### Download Functionality
- [ ] Click "Download All Plots (ZIP)" - should download ZIP file
- [ ] Click "Download Original Data (CSV)" - should download CSV
- [ ] Click "Download Processed Data (CSV)" - should download CSV
- [ ] Click individual "Download Plot" buttons under each visualization
- [ ] Click "Download Summary" buttons under each summary section
- [ ] Verify all downloaded files open correctly

### Navigation Flow
- [ ] On results page, click "Upload Another File" button
- [ ] Verify page navigates to upload section (not just home page)
- [ ] Should scroll to #upload-section smoothly
- [ ] Upload another file to test workflow

### Session Persistence
- [ ] Upload and analyze a file
- [ ] Wait 2 minutes
- [ ] Try downloading files - should still work
- [ ] Refresh the browser page
- [ ] Try downloading again - should work (within session timeout)

### Error Handling
- [ ] Try uploading empty file - should show error message
- [ ] Try uploading invalid file type - should show error
- [ ] Try downloading without analysis - should show appropriate message

### Mobile Responsiveness
- [ ] Open on mobile device or resize browser to mobile width
- [ ] Verify header scales appropriately
- [ ] Check navigation menu is accessible
- [ ] Test upload interface on mobile
- [ ] Verify results page layout on mobile
- [ ] Test download buttons on mobile

## Expected Results

### Successful Upload
- File validates successfully
- Analysis completes within 5-30 seconds (depending on file size)
- Results page displays with:
  - 3 stat cards showing analysis status
  - 2 collapsible summary sections
  - Multiple visualizations (histograms, box plots, pair plots)
  - Download buttons for all data and plots

### Successful Downloads
- **All Plots ZIP**: Contains all visualization PNG files
- **Original Data CSV**: Contains exact copy of uploaded data
- **Processed Data CSV**: Contains cleaned and processed data
- **Individual Plots**: High-quality PNG images
- **Summaries**: Text files with detailed statistics

### Proper Layout
- Header height: ~104px total (72px nav + 32px dashboard header)
- No content hidden behind sticky header
- Proper spacing between sections
- Stats cards display in responsive grid
- Visualizations display in 2-column grid (1-column on mobile)

## Common Issues and Solutions

### Issue: Downloads not working
**Solution**: Ensure you've analyzed a file first. Session must contain analysis data.

### Issue: Server won't start
**Solution**: 
1. Check if Django is installed: `python3 -c "import django"`
2. Install requirements: `pip install -r requirements.txt`
3. Run migrations: `python3 manage.py migrate`

### Issue: Layout looks broken
**Solution**: 
1. Clear browser cache
2. Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)
3. Check browser console for errors

### Issue: Upload fails
**Solution**:
1. Verify file is valid CSV or Excel format
2. Check file is not empty
3. Ensure file size is reasonable (< 100MB)
4. Check server logs for detailed error

## Performance Notes

- Small files (< 1MB): Analysis in 5-10 seconds
- Medium files (1-10MB): Analysis in 10-30 seconds
- Large files (> 10MB): May take 30-60 seconds

Visualization generation is the slowest part of the pipeline.

## Browser Compatibility

Tested and working on:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Security Notes

- CSRF protection enabled
- Session cookies HTTPOnly
- Secure file handling
- Input validation on upload

## Support

For issues or questions, check:
1. Server logs in terminal
2. Browser console (F12)
3. `/workspace/data-analyzer-project/FIXES_APPLIED.md` for implementation details
