import cv2
import numpy as np
import os
import torch
from PIL import Image as PILImage

class TableExtractor:

    def __init__(self, image_path, processor, model): 
        self.image_path = image_path
        self.processor_for_table_detection = processor
        self.model_for_table_detection = model

    def execute(self):
        self.read_crop_image()
        self.imag_normalization()
        self.removing_stamps()
        self.remove_noise()
        self.improved_image()
        self.table_detection()
        self.convert_image_to_grayscale()
        self.threshold_image()
        self.invert_image()
        self.dilate_image(iterations=2)
        self.find_contours()
        self.filter_contours_and_leave_only_rectangles()
        self.find_largest_contour_by_area()
        
        if cv2.contourArea(self.contour_with_max_area) < 0.06 * self.image.shape[0] * 0.5 * self.image.shape[1]:
            self.dilate_image(iterations=1)
            self.find_contours()
            self.filter_contours_and_leave_only_rectangles()
            self.find_largest_contour_by_area()
        
        self.order_points_in_the_contour_with_max_area()
        self.calculate_new_width_and_height_of_image()
        self.apply_perspective_transform()
        self.store_process_image("result/result.jpg", self.perspective_corrected_image)
        
        return self.perspective_corrected_image


    def read_crop_image(self):
        self.image = cv2.imdecode(np.fromfile(self.image_path, dtype=np.uint8), cv2.IMREAD_COLOR) #cv2.imread(self.image_path)
        self.image_crop = self.image[round(0.4*self.image.shape[0]):self.image.shape[0], 0:self.image.shape[1]]  

    def imag_normalization(self):
        norm_img = np.zeros((self.image_crop.shape[0], self.image_crop.shape[1])) 
        self.norm_image = cv2.normalize(self.image_crop, norm_img, 0, 255, cv2.NORM_MINMAX)

    def removing_stamps(self):
        denoised = cv2.medianBlur(self.norm_image, 3)
        gray = cv2.cvtColor(denoised, cv2.COLOR_BGR2GRAY)
        adaptiveThreshold = cv2.mean(self.norm_image)[0]
        color = cv2.cvtColor(denoised, cv2.COLOR_BGR2HLS)

        mask_gray = cv2.inRange(color, (90, 20, 70), (140, adaptiveThreshold, 255))
        dst = cv2.bitwise_and(gray, gray, mask=mask_gray)

        denoised = cv2.medianBlur(dst, 5)

        blur = cv2.blur(denoised, (3, 3))
        mask = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 0)
        mask = cv2.dilate(mask, None, iterations=1)

        self.image_without_stamps = self.norm_image.copy()
        self.image_without_stamps[mask == 255] = np.median(self.norm_image)

    def remove_noise(self):
        self.image_without_noise = cv2.fastNlMeansDenoisingColored(self.image_without_stamps, None, 5, 5, 7, 15)

    def improved_image(self):
        med = np.median(self.image_without_noise)
        if med <= 100:
            d = 64
        elif 100 < med < 180:
            d = 45
        else:
            d = 25
        alpha = 1 + round(d / med, 1)
        beta = round((255 - med) / 2)
        self.improved_image = cv2.convertScaleAbs(self.image_without_noise, alpha=alpha, beta=beta)

        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        self.improved_image = cv2.filter2D(self.improved_image, -1, kernel)

    def table_detection(self):
        image = PILImage.fromarray(self.improved_image)

        inputs = self.processor_for_table_detection(images=image, return_tensors="pt")
        outputs = self.model_for_table_detection(**inputs)

        # convert outputs (bounding boxes and class logits) to COCO API
        # keep detections with score > 0.9
        target_sizes = torch.tensor([image.size[::-1]])
        results = self.processor_for_table_detection.post_process_object_detection(outputs, target_sizes=target_sizes, threshold=0.9)[0]

        img = np.asarray(image)

        max_box = []
        max_area = 0
        for box in results["boxes"]:
            box = [round(i) for i in box.tolist()]
            area = (box[2] - box[0]) * (box[3] - box[1])
            if area > max_area:
                max_area = area
                max_box = box

        delta_x = round(0.03 * img.shape[1])
        delta_y = round(0.03 * img.shape[0])

        x1 = int((max_box[0]) - delta_x) if int((max_box[0]) - delta_x) >= 0 else 0
        y1 = int((max_box[1]) - delta_y) if int((max_box[1]) - delta_y) >= 0 else 0
        x2 = int((max_box[2]) + delta_x) if int((max_box[2]) + delta_x) <= img.shape[1] else img.shape[1]
        y2 = int((max_box[3]) + delta_y) if int((max_box[3]) + delta_y) <= img.shape[0] else img.shape[0]
        
        self.cut_table_image = img[y1:y2, x1:x2]         

    def convert_image_to_grayscale(self):
        self.grayscale_image = cv2.cvtColor(self.cut_table_image, cv2.COLOR_BGR2GRAY)

    def blur_image(self):
        self.blurred_image = cv2.blur(self.grayscale_image, (1, 1))

    def threshold_image(self):
        self.thresholded_image = cv2.adaptiveThreshold(self.grayscale_image,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,35,35)

    def invert_image(self):
        self.inverted_image = cv2.bitwise_not(self.thresholded_image)

    def dilate_image(self, iterations):
        self.dilated_image = cv2.dilate(self.inverted_image, None, iterations=iterations)

    def find_contours(self):
        self.contours, self.hierarchy = cv2.findContours(self.dilated_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

    def filter_contours_and_leave_only_rectangles(self):
        self.rectangular_contours = []
        for contour in self.contours:
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.04 * peri, True)
            if len(approx) == 4:
                self.rectangular_contours.append(approx)

    def find_largest_contour_by_area(self):
        max_area = 0
        self.contour_with_max_area = None
        for contour in self.rectangular_contours:
            area = cv2.contourArea(contour)
            if area > max_area:
                max_area = area
                self.contour_with_max_area = contour

    def order_points_in_the_contour_with_max_area(self):
        self.image_with_points_plotted = self.thresholded_image.copy()       
        if self.contour_with_max_area is not None:
            self.contour_with_max_area_ordered = self.order_points(self.contour_with_max_area)
        else:
            self.contour_with_max_area_ordered = None

    def calculate_new_width_and_height_of_image(self):
        existing_image_width = self.image.shape[1]
        existing_image_width_reduced_by_10_percent = int(existing_image_width * 0.9)
        
        if self.contour_with_max_area_ordered is not None:
            distance_between_top_left_and_top_right = self.calculateDistanceBetween2Points(self.contour_with_max_area_ordered[0],
                                                                                           self.contour_with_max_area_ordered[1])
            distance_between_top_left_and_bottom_left = self.calculateDistanceBetween2Points(self.contour_with_max_area_ordered[0],
                                                                                             self.contour_with_max_area_ordered[3])
            aspect_ratio = distance_between_top_left_and_bottom_left / distance_between_top_left_and_top_right
            self.new_image_width = existing_image_width_reduced_by_10_percent
            self.new_image_height = int(self.new_image_width * aspect_ratio)

    def apply_perspective_transform(self):
        if self.contour_with_max_area_ordered is not None:
            delta_x = round(0.01 * self.image.shape[1])
            delta_y = round(0.01 * self.image.shape[0])
            
            pts1 = np.float32(self.contour_with_max_area_ordered) 
            pts1[0][0] -= delta_x
            pts1[0][1] -= delta_y
            pts1[1][0] += delta_x
            pts1[1][1] -= delta_y
            pts1[2][0] += delta_x
            pts1[2][1] += delta_y
            pts1[3][0] -= delta_x
            pts1[3][1] += delta_y
            
            pts2 = np.float32([[0, 0], [self.new_image_width, 0], [self.new_image_width, self.new_image_height],
                               [0, self.new_image_height]])
            matrix = cv2.getPerspectiveTransform(pts1, pts2)
            ###### заменили self.thresholded_image на (self.cut_table_image
            self.perspective_corrected_image = cv2.warpPerspective(self.cut_table_image, matrix, 
                                                                   (self.new_image_width, self.new_image_height)) 
        else:
            self.perspective_corrected_image = self.thresholded_image.copy()


    def calculateDistanceBetween2Points(self, p1, p2):
        dis = ((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2) ** 0.5
        return dis
    
    def order_points(self, pts):
        # initialzie a list of coordinates that will be ordered
        # such that the first entry in the list is the top-left,
        # the second entry is the top-right, the third is the
        # bottom-right, and the fourth is the bottom-left
        pts = pts.reshape(4, 2)
        rect = np.zeros((4, 2), dtype="float32")

        # the top-left point will have the smallest sum, whereas
        # the bottom-right point will have the largest sum
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]

        # now, compute the difference between the points, the
        # top-right point will have the smallest difference,
        # whereas the bottom-left will have the largest difference
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]

        # return the ordered coordinates
        return rect
    
    def store_process_image(self, file_name, image):
        path = file_name
        cv2.imwrite(path, image)
